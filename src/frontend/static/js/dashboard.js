import { fetchPodcasts, fetchRSSData } from "../requests/podcastRequests.js"

document.addEventListener("DOMContentLoaded", function () {
	const podcastPopup = document.getElementById("podcast-popup")
	const podcastList = document.getElementById("podcast-list")
	const closePodcastPopup = document.getElementById("close-podcast-popup")
    let currentQuotes = [];
    let currentQuoteIndex = 0;
    let showingContext = false;

    // Create quote container
    let quoteContainer = document.querySelector(".quote-container");
    if (!quoteContainer) {
        quoteContainer = document.createElement("div");
        quoteContainer.className = "quote-container";
        document.querySelector(".card").appendChild(quoteContainer);
    }
    
    // Create quote display
    let quoteDisplay = document.getElementById("quote-display");
    if (!quoteDisplay) {
        quoteDisplay = document.createElement("div");
        quoteDisplay.id = "quote-display";
        quoteContainer.appendChild(quoteDisplay);
    }
    
    // Create navigation container
    let quoteNavigation = document.getElementById("quote-navigation");
    if (!quoteNavigation) {
        quoteNavigation = document.createElement("div");
        quoteNavigation.id = "quote-navigation";
        quoteContainer.appendChild(quoteNavigation);
    }

    document
		.getElementById("fileinput")
		.addEventListener("change", function (event) {
			const file = event.target.files[0]
			if (!file) return

			const reader = new FileReader()
			reader.onload = async function () {
				try {
					const text = reader.result;
                    // Show loading indicator
                    quoteDisplay.innerHTML = "<p>Analyzing transcript...</p>";
                    
					const response = await fetch("/generate_quote", {
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify({ 
                            text,
                            num_quotes: 5  // Request 5 quotes
                        }),
					});

					if (!response.ok) {
						const errorText = await response.text();
						console.error(
							"Server returned an error:",
							response.status,
							errorText
						);
						throw new Error(`Server error: ${response.status}`);
					}

					const result = await response.json();
                    currentQuotes = result.quotes || [];
                    currentQuoteIndex = 0;
                    showingContext = false;
                    
                    if (currentQuotes.length > 0) {
                        displayQuote(currentQuoteIndex);
                        setupQuoteNavigation();
                    } else {
                        quoteDisplay.innerHTML = "<p>No meaningful quotes found in the transcript.</p>";
                        quoteNavigation.innerHTML = "";
                    }
				} catch (error) {
					console.error("Error processing file:", error);
					quoteDisplay.innerHTML = "<p>Error: Could not generate quotes. See console for details.</p>";
                    quoteNavigation.innerHTML = "";
				}
			};
			reader.readAsText(file);
		});
        
    // Function to display a quote at the given index
    function displayQuote(index) {
        if (!currentQuotes || !currentQuotes.length) return;
        
        const quote = currentQuotes[index];
        let quoteText = typeof quote === 'string' ? quote : quote.text;
        let quoteContext = typeof quote === 'object' && quote.context ? quote.context : null;
        let position = typeof quote === 'object' && quote.position !== undefined ? quote.position : null;
        let timestamp = typeof quote === 'object' && quote.timestamp !== undefined ? quote.timestamp : null;
        let verified = typeof quote === 'object' ? quote.verified : true;
        
        let html = `<div class="quote">`;
        
        if (showingContext && quoteContext) {
            // Display with context
            html += `
                <div class="quote-context">
                    <strong>Context:</strong> ${highlightQuoteInContext(quoteContext, quoteText)}
                </div>
                <div class="context-toggle-button">Show Quote Only</div>
            `;
        } else {
            // Display just the quote
            html += `
                <blockquote>${quoteText}</blockquote>
                ${quoteContext ? `<div class="context-toggle-button">Show Context</div>` : ''}
            `;
        }
        
        // Add position, timestamp, and verification status
        html += `
            <div class="quote-details">
                ${position !== null ? `<div><strong>Position:</strong> ${position}</div>` : ''}
                ${timestamp !== null ? `<div><strong>Timestamp:</strong> ${timestamp}</div>` : ''}
                <div><strong>Verified:</strong> ${verified ? 'Yes' : 'No'}</div>
            </div>
            <div class="quote-counter">Quote ${index + 1} of ${currentQuotes.length}</div>
        `;
        
        html += `</div>`;
        
        quoteDisplay.innerHTML = html;
        
        // Add event listener to context toggle button
        const contextToggle = quoteDisplay.querySelector('.context-toggle-button');
        if (contextToggle) {
            contextToggle.addEventListener('click', () => {
                showingContext = !showingContext;
                displayQuote(currentQuoteIndex);
            });
        }
        
        // Update active state in navigation
        const navButtons = quoteNavigation.querySelectorAll('.quote-nav-dot');
        navButtons.forEach((btn, i) => {
            btn.classList.toggle('active', i === index);
        });
    }
    
    // Function to highlight the quote within its context
    function highlightQuoteInContext(context, quote) {
        if (!context || !quote) return context;
        
        // Escape special characters for regex
        const escapedQuote = quote.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        // Replace the quote with a highlighted version
        return context.replace(
            new RegExp(`(${escapedQuote})`, 'g'), 
            '<span class="highlighted-quote">$1</span>'
        );
    }
    
    // Set up quote navigation dots and controls
    function setupQuoteNavigation() {
        if (!currentQuotes || currentQuotes.length <= 1) {
            quoteNavigation.innerHTML = "";
            return;
        }
        
        // Create navigation HTML
        let navHTML = '<div class="quote-nav-prev">&#8592;</div><div class="quote-nav-dots">';
        
        for (let i = 0; i < currentQuotes.length; i++) {
            navHTML += `<div class="quote-nav-dot ${i === currentQuoteIndex ? 'active' : ''}" data-index="${i}"></div>`;
        }
        
        navHTML += '</div><div class="quote-nav-next">&#8594;</div>';
        quoteNavigation.innerHTML = navHTML;
        
        // Add event listeners
        quoteNavigation.querySelector('.quote-nav-prev').addEventListener('click', () => {
            currentQuoteIndex = (currentQuoteIndex - 1 + currentQuotes.length) % currentQuotes.length;
            displayQuote(currentQuoteIndex);
        });
        
        quoteNavigation.querySelector('.quote-nav-next').addEventListener('click', () => {
            currentQuoteIndex = (currentQuoteIndex + 1) % currentQuotes.length;
            displayQuote(currentQuoteIndex);
        });
        
        // Add event listeners to dots
        quoteNavigation.querySelectorAll('.quote-nav-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                currentQuoteIndex = parseInt(dot.dataset.index);
                displayQuote(currentQuoteIndex);
            });
        });
    }

	async function fetchAndDisplayPodcasts() {
		try {
			console.log("Fetching podcasts...")
			const data = await fetchPodcasts()
			const podcasts = data.podcast // Access the podcast property
			console.log("Podcasts fetched:", podcasts)
			podcastList.innerHTML = "" // Clear existing content
			for (const podcast of podcasts) {
				const podcastItem = document.createElement("li")
				podcastItem.className = "podcast-item"
				podcastItem.style.cursor = "pointer" // Change cursor to pointer on hover

				// Fetch additional information from the RSS feed
				let imageUrl =
					"{{ url_for('static', filename='images/mock-avatar.jpeg') }}"
				try {
					const rssData = await fetchRSSData(podcast.rssFeed)
					console.log("RSS Data:", rssData) // Log all RSS data
					imageUrl = rssData.imageUrl || imageUrl
				} catch (error) {
					console.error("Error fetching RSS data:", error)
				}

				podcastItem.innerHTML = `
          <span class="podcast-title">${podcast.podName}</span>
          <img src="${imageUrl}" alt="${podcast.podName}" class="podcast-image" />
          <div class="podcast-item-actions">
            <button class="view-btn" data-id="${podcast._id}">View</button>
          </div>
        `
				// Add click event to the entire podcast item that redirects to podcast management view details
				podcastItem.addEventListener("click", (e) => {
					e.stopPropagation()
					// Redirect to podcast management view details page for the selected podcast
					window.location.href = `/podcastmanagement?podcastId=${podcast._id}`
				})

				podcastList.appendChild(podcastItem)
			}
		} catch (error) {
			console.error("Error fetching podcasts:", error)
		}
	}
	window.fetchAndDisplayPodcasts = fetchAndDisplayPodcasts // Expose the function to window

	// Fetch and display podcasts when the podcast popup is shown
	podcastPopup.addEventListener("click", function (e) {
		if (e.target === podcastPopup) {
			fetchAndDisplayPodcasts()
		}
	})

	// Close podcast popup on clicking the close button
	closePodcastPopup.addEventListener("click", function () {
		podcastPopup.style.display = "none"
	})

	// Close podcast popup if clicking outside the popup-content
	podcastPopup.addEventListener("click", function (e) {
		if (e.target === podcastPopup) {
			podcastPopup.style.display = "none"
		}
	})
})
