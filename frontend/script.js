document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const storyForm = document.getElementById("story-form")
  const generateBtn = document.getElementById("generate-btn")
  const btnText = document.querySelector(".btn-text")
  const btnLoading = document.querySelector(".btn-loading")
  const storyOutput = document.getElementById("story-output")
  const storyText = document.getElementById("story-text")
  const storyImageContainer = document.getElementById("story-image-container")
  const storyImage = document.getElementById("story-image")
  const imageLoading = document.querySelector(".image-loading")
  const storyAudioContainer = document.getElementById("story-audio-container")
  const storyAudio = document.getElementById("story-audio")
  const audioLoading = document.querySelector(".audio-loading")
  const audioControls = document.querySelector(".audio-controls")
  const generateAudioBtn = document.getElementById("generate-audio-btn")
  const lengthSlider = document.getElementById("length")
  const lengthValue = document.getElementById("length-value")
  const generateImageCheckbox = document.getElementById("generate-image")
  const generateAudioCheckbox = document.getElementById("generate-audio")
  const copyBtn = document.getElementById("copy-btn")
  const downloadBtn = document.getElementById("download-btn")
  const regenerateBtn = document.getElementById("regenerate-btn")
  const shareBtn = document.getElementById("share-btn")
  const themeToggleBtn = document.getElementById("theme-toggle-btn")
  const toast = document.getElementById("toast")
  const backendError = document.getElementById("backend-error")
  const retryConnectionBtn = document.getElementById("retry-connection")
  const currentYearSpan = document.getElementById("current-year")

  // Set current year in footer
  if (currentYearSpan) {
    currentYearSpan.textContent = new Date().getFullYear()
  }

  // API URL - Change this to your backend URL
  const API_URL = "http://localhost:5500/api"

  // State variables
  let currentStory = null
  let currentImage = null
  let currentAudio = null
  let currentStoryId = null
  let backendAvailable = true
  let isGenerating = false

  // Check for saved theme
  if (
    localStorage.getItem("theme") === "dark" ||
    (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches)
  ) {
    document.body.classList.add("dark-mode")
  }

  // Event Listeners
  if (storyForm) storyForm.addEventListener("submit", handleFormSubmit)
  if (lengthSlider) lengthSlider.addEventListener("input", updateLengthValue)
  if (copyBtn) copyBtn.addEventListener("click", copyToClipboard)
  if (downloadBtn) downloadBtn.addEventListener("click", downloadStory)
  if (regenerateBtn) regenerateBtn.addEventListener("click", regenerateStory)
  if (shareBtn) shareBtn.addEventListener("click", shareStory)
  if (themeToggleBtn) themeToggleBtn.addEventListener("click", toggleTheme)
  if (retryConnectionBtn) retryConnectionBtn.addEventListener("click", checkBackendHealth)
  if (generateAudioBtn) generateAudioBtn.addEventListener("click", handleGenerateAudio)

  // Update length value display
  function updateLengthValue() {
    if (lengthValue && lengthSlider) {
      lengthValue.textContent = lengthSlider.value
    }
  }

  // Toggle theme
  function toggleTheme() {
    document.body.classList.toggle("dark-mode")
    localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light")
  }

  // Handle form submission
  async function handleFormSubmit(e) {
    e.preventDefault()

    if (isGenerating) {
      showToast("A story is already being generated. Please wait.", "warning")
      return
    }

    if (!backendAvailable) {
      showToast("Backend server is not available. Please check your connection.", "error")
      return
    }

    // Get form data
    const formData = new FormData(storyForm)
    const prompt = formData.get("prompt")
    const genre = formData.get("genre")
    const tone = formData.get("tone")
    const length = formData.get("length")
    const generateImage = generateImageCheckbox ? generateImageCheckbox.checked : false
    const generateAudio = generateAudioCheckbox ? generateAudioCheckbox.checked : false

    // Validate prompt
    if (!prompt || prompt.trim().length < 5) {
      showToast("Please enter a story prompt with at least 5 characters.", "error")
      return
    }

    // Show loading state
    setLoadingState(true)
    isGenerating = true

    // Reset story output
    if (storyText) storyText.textContent = ""
    if (storyImage) storyImage.src = ""
    if (storyImageContainer) storyImageContainer.classList.add("hidden")
    if (storyAudioContainer) storyAudioContainer.classList.add("hidden")

    // Show loading for image generation
    if (generateImage && storyImageContainer && imageLoading) {
      storyImageContainer.classList.remove("hidden")
      imageLoading.classList.remove("hidden")
      if (storyImage) storyImage.classList.add("hidden")
      imageLoading.innerHTML = `
        <div class="loading-animation">
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
        </div>
        <span class="loading-text">Generating SVG artwork with Gemini...</span>
      `
    }

    // Show loading for audio generation
    if (generateAudio && storyAudioContainer && audioLoading) {
      storyAudioContainer.classList.remove("hidden")
      audioLoading.classList.remove("hidden")
      if (audioControls) audioControls.classList.add("hidden")
      audioLoading.innerHTML = `
        <div class="loading-animation">
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
        </div>
        <span class="loading-text">Generating audio with OpenAI TTS...</span>
      `
    }

    try {
      const result = await generateStory(prompt, genre, tone, length, generateImage, generateAudio)

      // Update story text
      if (storyText && result.story) {
        storyText.textContent = result.story
        currentStory = result.story
        currentStoryId = result.storyId
      }

      // Handle image result
      if (generateImage) {
        if (result.imageUrl && storyImage && imageLoading) {
          storyImage.src = `${API_URL.replace("/api", "")}${result.imageUrl}`
          storyImage.classList.remove("hidden")
          imageLoading.classList.add("hidden")
          currentImage = result.imageUrl
          showToast(`SVG artwork generated successfully with Gemini!`)
        } else if (result.imageError && imageLoading) {
          imageLoading.innerHTML = `<i class="fas fa-exclamation-triangle"></i><span>${result.imageError}</span>`
          showToast(result.imageError, "warning")
        }
      }

      // Handle audio result
      if (generateAudio) {
        if (result.audioUrl && storyAudio && audioLoading && audioControls) {
          storyAudio.src = `${API_URL.replace("/api", "")}${result.audioUrl}`
          audioControls.classList.remove("hidden")
          audioLoading.classList.add("hidden")
          currentAudio = result.audioUrl
          showToast(`Audio generated successfully with OpenAI TTS!`)
        } else if (result.audioError && audioLoading) {
          audioLoading.innerHTML = `<i class="fas fa-exclamation-triangle"></i><span>${result.audioError}</span>`
          showToast(result.audioError, "warning")
        }
      }

      // Show story output
      if (storyOutput) {
        storyOutput.classList.remove("hidden")
        // Scroll to story
        storyOutput.scrollIntoView({ behavior: "smooth" })
      }

      showToast("Story generated successfully!")
    } catch (error) {
      console.error("Error generating story:", error)

      // Display error message from API if available
      let errorMessage = "Failed to generate story. Please try again."
      if (error.response && error.response.data && error.response.data.error) {
        errorMessage = error.response.data.error
      } else if (typeof error === "string") {
        errorMessage = error
      } else if (error.message) {
        errorMessage = error.message
      }

      showToast(errorMessage, "error")
      if (storyImageContainer) storyImageContainer.classList.add("hidden")
      if (storyAudioContainer) storyAudioContainer.classList.add("hidden")

      // Show error in story output area
      if (storyOutput && storyText) {
        storyOutput.classList.remove("hidden")
        storyText.innerHTML = `<div class="error-message">
          <h3>Error Generating Story</h3>
          <p>${errorMessage}</p>
          <p>Please try again with a different prompt or check your connection.</p>
        </div>`
      }
    } finally {
      setLoadingState(false)
      isGenerating = false
    }
  }

  // Generate story using backend API
  async function generateStory(prompt, genre, tone, length, generateImage, generateAudio) {
    try {
      const response = await fetch(`${API_URL}/generate-story`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          genre,
          tone,
          length: Number.parseInt(length),
          generateImage,
          generateAudio,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to generate story")
      }

      return await response.json()
    } catch (error) {
      console.error("API Error:", error)
      throw error
    }
  }

  // Handle generate audio button click
  async function handleGenerateAudio() {
    if (!currentStory) {
      showToast("No story available to generate audio for.", "warning")
      return
    }

    if (!audioLoading || !audioControls) {
      showToast("Audio controls not available.", "error")
      return
    }

    try {
      audioLoading.classList.remove("hidden")
      audioControls.classList.add("hidden")
      audioLoading.innerHTML = `
        <div class="loading-animation">
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
          <div class="loading-circle"></div>
        </div>
        <span class="loading-text">Generating audio with OpenAI TTS...</span>
      `

      const response = await fetch(`${API_URL}/generate-audio`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: currentStory,
          storyId: currentStoryId,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to generate audio")
      }

      const result = await response.json()

      if (result.audioUrl && storyAudio) {
        storyAudio.src = `${API_URL.replace("/api", "")}${result.audioUrl}`
        audioControls.classList.remove("hidden")
        audioLoading.classList.add("hidden")
        currentAudio = result.audioUrl
        showToast("Audio generated successfully with OpenAI TTS!")
      } else {
        throw new Error(result.error || "Failed to generate audio")
      }
    } catch (error) {
      console.error("Audio generation error:", error)
      audioLoading.innerHTML = `<i class="fas fa-exclamation-triangle"></i><span>${error.message}</span>`
      showToast(error.message, "error")
    }
  }

  // Copy story to clipboard
  function copyToClipboard() {
    if (!currentStory) {
      showToast("No story to copy.", "warning")
      return
    }

    navigator.clipboard
      .writeText(currentStory)
      .then(() => showToast("Story copied to clipboard!"))
      .catch((err) => {
        console.error("Failed to copy text: ", err)
        showToast("Failed to copy story to clipboard.", "error")
      })
  }

  // Download story as text file
  function downloadStory() {
    if (!currentStory) {
      showToast("No story to download.", "warning")
      return
    }

    const blob = new Blob([currentStory], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `ai-story-${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    showToast("Story downloaded successfully!")
  }

  // Regenerate story
  function regenerateStory() {
    const event = new Event("submit")
    handleFormSubmit(event)
  }

  // Share story
  async function shareStory() {
    if (!currentStory) {
      showToast("No story to share.", "warning")
      return
    }

    if (navigator.share) {
      try {
        await navigator.share({
          title: "AI Generated Story",
          text: currentStory,
        })
        showToast("Story shared successfully!")
      } catch (error) {
        console.error("Error sharing:", error)
        if (error.name !== "AbortError") {
          showToast("Failed to share story", "error")
        }
      }
    } else {
      copyToClipboard()
      showToast("Story copied to clipboard for sharing!")
    }
  }

  // Set loading state
  function setLoadingState(isLoading) {
    if (btnText && btnLoading && generateBtn) {
      if (isLoading) {
        btnText.classList.add("hidden")
        btnLoading.classList.remove("hidden")
        generateBtn.disabled = true
        if (regenerateBtn) regenerateBtn.disabled = true
      } else {
        btnText.classList.remove("hidden")
        btnLoading.classList.add("hidden")
        generateBtn.disabled = false
        if (regenerateBtn) regenerateBtn.disabled = false
      }
    }
  }

  // Show toast notification
  function showToast(message, type = "success") {
    if (!toast) return

    const toastIcon = document.querySelector(".toast-icon")
    const toastMessage = document.querySelector(".toast-message")
    const toastContent = document.querySelector(".toast-content")

    if (!toastIcon || !toastMessage || !toastContent) return

    // Set icon and color based on type
    if (type === "error") {
      toastIcon.className = "fas fa-exclamation-circle toast-icon"
      toastContent.style.borderLeftColor = "var(--error-500)"
      toastIcon.style.color = "var(--error-500)"
    } else if (type === "warning") {
      toastIcon.className = "fas fa-exclamation-triangle toast-icon"
      toastContent.style.borderLeftColor = "var(--warning-500)"
      toastIcon.style.color = "var(--warning-500)"
    } else {
      toastIcon.className = "fas fa-check-circle toast-icon"
      toastContent.style.borderLeftColor = "var(--success-500)"
      toastIcon.style.color = "var(--success-500)"
    }

    toastMessage.textContent = message
    toast.classList.remove("hidden")
    toast.classList.add("show")

    setTimeout(() => {
      toast.classList.remove("show")
      setTimeout(() => toast.classList.add("hidden"), 300)
    }, 4000)
  }

  // Check if backend is available
  async function checkBackendHealth() {
    try {
      if (backendError) backendError.classList.add("hidden")

      const response = await fetch(`${API_URL}/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      backendAvailable = true

      // Check Gemini API
      if (!data.gemini_api_configured) {
        showToast("Gemini API key not configured. Please check server setup.", "error")
      } else if (!data.gemini_working) {
        showToast("Gemini API connection issues detected.", "warning")
        if (data.gemini_error) {
          console.error("Gemini API error:", data.gemini_error)
        }
      } else {
        showToast("Backend connection successful! Gemini API is working.")
      }

      // Check OpenAI API with detailed feedback
      if (!data.openai_api_configured) {
        showToast("OpenAI API key not configured. Audio generation will not be available.", "warning")
        console.log("OpenAI API key not found in environment variables")
      } else if (!data.openai_working) {
        showToast(`OpenAI API connection failed: ${data.openai_error || "Unknown error"}`, "error")
        console.error("OpenAI API error:", data.openai_error)

        // Test OpenAI TTS specifically
        testOpenAITTS()
      } else {
        showToast("OpenAI TTS available for audio generation!")
      }

      // Check SVG image generation
      if (data.image_generation_available) {
        showToast("SVG image generation available with Gemini!")
      } else {
        showToast("SVG image generation not available. Check Gemini API configuration.", "warning")
      }

      return true
    } catch (error) {
      console.error("Backend health check failed:", error)
      backendAvailable = false
      if (backendError) backendError.classList.remove("hidden")
      showToast("Cannot connect to backend server", "error")
      return false
    }
  }

  // Add this new function to test OpenAI TTS specifically
  async function testOpenAITTS() {
    try {
      console.log("Testing OpenAI TTS specifically...")

      const response = await fetch(`${API_URL}/test-audio`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: "Test audio generation",
        }),
      })

      const result = await response.json()

      if (result.success) {
        showToast("OpenAI TTS test successful!", "success")
        console.log("OpenAI TTS test passed:", result)
      } else {
        showToast(`OpenAI TTS test failed: ${result.error}`, "error")
        console.error("OpenAI TTS test failed:", result)
      }
    } catch (error) {
      console.error("OpenAI TTS test error:", error)
      showToast("OpenAI TTS test failed with network error", "error")
    }
  }

  // Initialize length value display
  updateLengthValue()

  // Check backend health on page load
  checkBackendHealth()
})
