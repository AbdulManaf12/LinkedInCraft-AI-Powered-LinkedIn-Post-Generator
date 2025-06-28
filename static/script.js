class LinkedInPostGenerator {
  constructor() {
    this.initializeElements();
    this.bindEvents();
  }

  initializeElements() {
    this.form = document.getElementById("postForm");
    this.topicInput = document.getElementById("topicInput");
    this.generateBtn = document.getElementById("generateBtn");
    this.outputSection = document.getElementById("outputSection");
    this.loadingState = document.getElementById("loadingState");
    this.resultCard = document.getElementById("resultCard");
    this.postContent = document.getElementById("postContent");
    this.copyBtn = document.getElementById("copyBtn");
    this.shareBtn = document.getElementById("shareBtn");
    this.toast = document.getElementById("toast");
  }

  bindEvents() {
    this.form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.generatePost();
    });

    this.copyBtn.addEventListener("click", () => {
      this.copyToClipboard();
    });

    this.shareBtn.addEventListener("click", () => {
      this.shareOnLinkedIn();
    });

    this.topicInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.generatePost();
      }
    });
  }

  async generatePost() {
    const topic = this.topicInput.value.trim();

    if (!topic) {
      this.showToast("Please enter a topic first!", "error");
      return;
    }

    console.log("Starting post generation for topic:", topic);
    this.showOutput();
    this.showLoading();

    try {
      // Try calling the local Flask app first, then fallback to external API
      let response;

      try {
        // First try the local Flask app
        const formData = new FormData();
        formData.append("query", topic);

        response = await fetch("/generate", {
          method: "POST",
          body: formData,
        });
      } catch (localError) {
        console.log("Local API failed, trying external API...");

        // Fallback to external API with proper CORS handling
        const formData = new FormData();
        formData.append("query", topic);

        response = await fetch("https://manafai.pythonanywhere.com/generate", {
          method: "POST",
          mode: "cors",
          headers: {
            Accept: "application/json",
          },
          body: formData,
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      console.log("Generated Post:", data.content);

      this.displayPost(data.content);
    } catch (error) {
      console.error("Error generating post:", error);
      this.hideLoading();
      let errorMessage = "Failed to generate post";
      if (error.message.includes("Failed to fetch")) {
        errorMessage = "Network error - please check your internet connection";
      } else if (error.message.includes("CORS")) {
        errorMessage = "CORS error - API configuration issue";
      } else {
        errorMessage = `Error: ${error.message}`;
      }

      this.showToast(errorMessage, "error");
    }
  }

  showOutput() {
    this.outputSection.classList.add("show");
    this.outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  showLoading() {
    this.loadingState.style.display = "block";
    this.resultCard.classList.remove("show");
  }

  hideLoading() {
    this.loadingState.style.display = "none";
  }

  async displayPost(post) {
    this.hideLoading();
    this.postContent.textContent = post;
    this.resultCard.classList.add("show");
  }

  async copyToClipboard() {
    try {
      const text = this.postContent.textContent;
      await navigator.clipboard.writeText(text);
      this.showToast("Post copied to clipboard! 📋");

      // Visual feedback on button
      const originalText = this.copyBtn.innerHTML;
      this.copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
      this.copyBtn.style.background = "#28a745";

      setTimeout(() => {
        this.copyBtn.innerHTML = originalText;
        this.copyBtn.style.background = "";
      }, 2000);
    } catch (err) {
      this.showToast("Failed to copy. Please try again.", "error");
    }
  }

  shareOnLinkedIn() {
    const text = encodeURIComponent(this.postContent.textContent);
    const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
      window.location.href
    )}&summary=${text}`;
    window.open(url, "_blank", "width=600,height=600");
  }

  showToast(message, type = "success") {
    this.toast.innerHTML = `
            <i class="fas fa-${
              type === "success" ? "check-circle" : "exclamation-circle"
            }"></i>
            <span>${message}</span>
        `;
    this.toast.style.background = type === "success" ? "#28a745" : "#dc3545";
    this.toast.classList.add("show");

    setTimeout(() => {
      this.toast.classList.remove("show");
    }, 3000);
  }

  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new LinkedInPostGenerator();
});

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("scroll", () => {
    const scrolled = window.pageYOffset;
    const rate = scrolled * -0.5;
    document.body.style.backgroundPosition = `center ${rate}px`;
  });

  const input = document.getElementById("topicInput");
  const placeholders = [
    "Enter your blog post topic or news headline...",
    'e.g., "Artificial Intelligence in Healthcare"',
    'e.g., "Remote Work Best Practices"',
    'e.g., "Sustainable Business Strategies"',
    'e.g., "Digital Transformation Trends"',
  ];

  let currentPlaceholder = 0;

  setInterval(() => {
    if (document.activeElement !== input) {
      currentPlaceholder = (currentPlaceholder + 1) % placeholders.length;
      input.placeholder = placeholders[currentPlaceholder];
    }
  }, 3000);
});
