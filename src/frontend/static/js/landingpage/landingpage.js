document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Color Thief Debug Started");

    if (typeof ColorThief === "undefined") {
        console.error("❌ Error: ColorThief library failed to load.");
        return;
    }

    const logoImg = document.getElementById("podcast-logo");
    if (!logoImg) {
        console.error("❌ Error: podcast-logo image not found in DOM!");
        return;
    }

    console.log("✅ Logo image found, source:", logoImg.src);

    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.src = logoImg.src;

    img.onload = function () {
        console.log("✅ Image successfully loaded:", img.src);

        try {
            const colorThief = new ColorThief();
            const palette = colorThief.getPalette(img, 5);  // Extract 5 colors for a richer theme
            
            if (!palette || palette.length < 3) {
                console.error("❌ Error: No colors extracted.");
                return;
            }

            console.log("🎨 Extracted Colors:", palette);

            // Assign extracted colors to variables
            const primaryColor = `rgb(${palette[0].join(",")})`;  // Main color (background)
            const secondaryColor = `rgb(${palette[1].join(",")})`; // Section background
            const accentColor = `rgb(${palette[2].join(",")})`;   // Buttons/links
            const textColor = `rgb(${palette[3].join(",")})`;     // Contrast text
            const highlightColor = `rgb(${palette[4].join(",")})`; // Extra details

            // 🌟 Apply to the whole theme
            document.body.style.background = primaryColor;
            document.body.style.color = textColor;

            // Navbar & Header
            document.querySelector("header").style.backgroundColor = secondaryColor;
            document.querySelector(".navbar").style.backgroundColor = secondaryColor;

            // Podcast Header Section
            document.getElementById("podcast-header").style.background = `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`;

            // About Section
            document.querySelector(".about-section").style.backgroundColor = secondaryColor;

            // Latest Episodes Section
            document.querySelector(".latest-episodes-section").style.backgroundColor = primaryColor;

            // Footer
            document.querySelector("footer").style.backgroundColor = secondaryColor;
            document.querySelector("footer").style.color = textColor;

            // Buttons & Links
            let buttons = document.querySelectorAll(".subscribe-btn, .listen-btn, .sponsor-btn");
            buttons.forEach(btn => {
                btn.style.backgroundColor = accentColor;
                btn.style.color = textColor;
                btn.style.border = `2px solid ${highlightColor}`;
            });

            // Social Media Icons
            let icons = document.querySelectorAll("#host-social a");
            icons.forEach(icon => {
                icon.style.color = highlightColor;
            });

            console.log("🎨 Theme applied successfully!");

        } catch (error) {
            console.error("❌ Error in Color Thief:", error);
        }
    };

    img.onerror = function () {
        console.error("❌ Error: Could not load the logo image.");
    };
});
