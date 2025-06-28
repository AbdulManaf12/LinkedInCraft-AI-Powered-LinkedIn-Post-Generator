import json
from typing import Optional, Iterator
from pydantic import BaseModel, Field
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.workflow import Workflow, RunResponse, RunEvent
from phi.storage.workflow.sqlite import SqlWorkflowStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.utils.log import logger
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class NewsArticle(BaseModel):
    title: str = Field(..., description="Title of the article.")
    url: str = Field(..., description="Link to the article.")
    summary: Optional[str] = Field(..., description="Summary of the article if available.")

class SearchResults(BaseModel):
    articles: list[NewsArticle]

class BlogPostGenerator(Workflow):
    # Define an Agent that will search the web for a topic
    searcher: Agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[DuckDuckGo()],
        instructions=["Given a topic, search for the top 5 articles."],
        response_model=SearchResults,
        structured_outputs=True,
    )

    # Define an Agent that will write the blog post and format it for LinkedIn
    writer: Agent = Agent(
        model=OpenAIChat(id="gpt-4"),
        instructions=[
            "You will be provided with a topic and a list of top articles on that topic.",
            "Carefully read each article and generate a LinkedIn post based on this topic.",
            "The LinkedIn post should include: a catchy intro, key insights, industry-leading opinions, and a call to action.",
            "Ensure that the post is engaging and formatted well for LinkedIn, using emojis and proper sectioning.",
            "Provide key takeaways in bullet points, a link to the blog post, and a prompt for comments.",
        ],
        markdown=True,
    )

    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        """This is where the main logic of the workflow is implemented."""

        logger.info(f"Generating a LinkedIn post on: {topic}")

        # Step 1: Use the cached LinkedIn post if use_cache is True
        if use_cache:
            cached_linkedin_post = self.get_cached_blog_post(topic)
            if cached_linkedin_post:
                yield RunResponse(content=cached_linkedin_post, event=RunEvent.workflow_completed)
                return

        # Step 2: Search the web for articles on the topic
        search_results: Optional[SearchResults] = self.get_search_results(topic)
        if search_results is None or len(search_results.articles) == 0:
            yield RunResponse(
                event=RunEvent.workflow_completed,
                content=f"Sorry, could not find any articles on the topic: {topic}",
            )
            return

        # Step 3: Write the LinkedIn post
        yield from self.write_linkedin_post(topic, search_results)

    def get_cached_blog_post(self, topic: str) -> Optional[str]:
        """Get the cached LinkedIn post for a topic."""

        logger.info("Checking if cached LinkedIn post exists")
        return self.session_state.get("linkedin_posts", {}).get(topic)

    def add_blog_post_to_cache(self, topic: str, blog_post: Optional[str]):
        """Add a LinkedIn post to the cache."""

        logger.info(f"Saving LinkedIn post for topic: {topic}")
        self.session_state.setdefault("linkedin_posts", {})
        self.session_state["linkedin_posts"][topic] = blog_post

    def get_search_results(self, topic: str) -> Optional[SearchResults]:
        """Get the search results for a topic."""

        MAX_ATTEMPTS = 3

        for attempt in range(MAX_ATTEMPTS):
            try:
                searcher_response: RunResponse = self.searcher.run(topic)

                # Check if we got a valid response
                if not searcher_response or not searcher_response.content:
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Empty searcher response")
                    continue
                # Check if the response is of the expected SearchResults type
                if not isinstance(searcher_response.content, SearchResults):
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Invalid response type")
                    continue

                article_count = len(searcher_response.content.articles)
                logger.info(f"Found {article_count} articles on attempt {attempt + 1}")
                return searcher_response.content

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {str(e)}")

        logger.error(f"Failed to get search results after {MAX_ATTEMPTS} attempts")
        return None

    def write_linkedin_post(self, topic: str, search_results: SearchResults) -> Iterator[RunResponse]:
        """Write a LinkedIn post on a topic."""

        logger.info("Writing LinkedIn post")
        # Prepare the input for the writer
        writer_input = {"topic": topic, "articles": [v.model_dump() for v in search_results.articles]}
        # Run the writer to generate the LinkedIn post
        yield from self.writer.run(json.dumps(writer_input, indent=4), stream=True)
        # Save the LinkedIn post in the cache
        self.add_blog_post_to_cache(topic, self.writer.run_response.content)

def generate_post(query):
    """Generate a LinkedIn post based on a query."""
    url_safe_topic = query.lower().replace(" ", "-")

    generate_linkedin_post = BlogPostGenerator(
        session_id=f"generate-linkedin-post-on-{url_safe_topic}",
        storage=SqlWorkflowStorage(
            table_name="generate_linkedin_post_workflows",
            db_file="tmp/workflows.db",
        ),
    )
    linkedin_post: Iterator[RunResponse] = generate_linkedin_post.run(topic=query, use_cache=True)

    text = ""
    for response in linkedin_post:
        if response.content:
            text += response.content

    return text