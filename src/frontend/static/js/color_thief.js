function applyColorThiefToLandingPage(logoSelector) {
    console.log("🚀 Color Thief Debug Started for Landing Page");

    if (typeof ColorThief === "undefined") {
        console.error("❌ Error: ColorThief library failed to load.");
        return;
    }

    const logoImg = document.querySelector(logoSelector);

    if (!logoImg || !logoImg.src) {
        console.error("❌ Error: No valid podcast logo found!");
        return;
    }

    console.log("✅ Logo image found, source:", logoImg.src);

    let img = new Image();
    img.crossOrigin = "Anonymous";
    // Check if it's a Base64 image or an external URL
    if (logoImg.src.startsWith("data:image")) {
        img.src = logoImg.src; // ✅ Direct Base64 Image
    } else {
        img.src = logoImg.src; // ✅ External URL
    }

    img.onload = function () {
        console.log("✅ Image successfully loaded:", img.src);
        try {
            const colorThief = new ColorThief();
            const palette = colorThief.getPalette(img, 5); // Extract 5 colors

            if (!palette || palette.length < 3) {
                console.error("❌ Error: No colors extracted.");
                return;
            }

            console.log("🎨 Extracted Colors:", palette);

            // ✅ Assign extracted colors
            const primaryColor = `rgb(${palette[0].join(",")})`;  // Main color
            const secondaryColor = `rgb(${palette[1].join(",")})`; // Section background
            const accentColor = `rgb(${palette[2].join(",")})`;   // Buttons/links
            const textColor = `rgb(${palette[3].join(",")})`;     // Contrast text
            const highlightColor = `rgb(${palette[4].join(",")})`; // Extra details

            // ✅ Apply colors to Navbar
            document.querySelector(".navbar").style.backgroundColor = secondaryColor;

            // ✅ Apply colors to About Section
            document.querySelector(".about-section").style.backgroundColor = secondaryColor;
            document.querySelector(".about-section").style.color = textColor;

            // ✅ Apply colors to Latest Episodes Section
            document.querySelector(".latest-episodes-section").style.backgroundColor = primaryColor;
            document.querySelector(".latest-episodes-section").style.color = textColor;

            // ✅ Apply colors to Exclusive Episodes Section
            document.querySelector(".exclusive-episodes-section").style.backgroundColor = secondaryColor;
            document.querySelector(".exclusive-episodes-section").style.color = textColor;

            // ✅ Apply colors to Guest & Sponsor Section
            document.querySelector(".guest-sponsor-section").style.backgroundColor = primaryColor;
            document.querySelector(".guest-sponsor-section").style.color = textColor;

            // ✅ Apply colors to Extra Section
            document.querySelector(".extra-section").style.backgroundColor = secondaryColor;
            document.querySelector(".extra-section").style.color = textColor;

            // ✅ Apply colors to Footer
            document.querySelector("footer.section-darkgrey").style.backgroundColor = primaryColor;
            document.querySelector("footer.section-darkgrey").style.color = textColor;

            console.log("✅ Landing Page Theme Applied!");

        } catch (error) {
            console.error("❌ Error in Color Thief:", error);
        }
    };

    img.onerror = function () {
        console.error("❌ Error: Could not load the podcast logo.");
    };
}


function applyColorThiefToEpisodePage(logoSelector) {
    console.log("🚀 Color Thief Debug Started for Episode Page");

    if (typeof ColorThief === "undefined") {
        console.error("❌ Error: ColorThief library failed to load.");
        return;
    }

    const logoImg = document.querySelector(logoSelector);

    if (!logoImg || !logoImg.src) {
        console.error("❌ Error: No valid podcast logo found!");
        return;
    }

    console.log("✅ Logo image found, source:", logoImg.src);

    let img = new Image();
    img.crossOrigin = "Anonymous";
    img.src = logoImg.src;

    img.onload = function () {
        console.log("✅ Image successfully loaded:", img.src);
        try {
            const colorThief = new ColorThief();
            const palette = colorThief.getPalette(img, 5); // Extract 5 colors

            if (!palette || palette.length < 5) {
                console.error("❌ Error: Not enough colors extracted.");
                return;
            }

            console.log("🎨 Extracted Colors:", palette);

            // ✅ Assign extracted colors
            const primaryColor = `rgb(${palette[0].join(",")})`;  // Main background
            const secondaryColor = `rgb(${palette[1].join(",")})`; // Alternating sections
            const accentColor = `rgb(${palette[2].join(",")})`;   // Buttons/highlights
            const textColor = `rgb(${palette[3].join(",")})`;     // Text color
            const highlightColor = `rgb(${palette[4].join(",")})`; // Extra details

            // ✅ Apply colors to the Navbar
            document.querySelector(".navbar").style.backgroundColor = secondaryColor;

            // ✅ Apply colors to ALL sections (Zig-Zag Pattern)
            const sections = document.querySelectorAll(
                ".episode-banner, .transcript, .audio-player, .key-learnings, .faq, .shorts, .guest-about-section"
            );

            sections.forEach((section, index) => {
                if (index % 2 === 0) {
                    section.style.backgroundColor = primaryColor;
                    section.style.color = textColor;
                } else {
                    section.style.backgroundColor = secondaryColor;
                    section.style.color = textColor;
                }
            });

            // ✅ Apply colors to Episode Banner
            document.querySelector(".episode-banner").style.background = `linear-gradient(to bottom, ${primaryColor}, ${secondaryColor})`;

            // ✅ Apply colors to Audio Player
            document.querySelector(".audio-player").style.backgroundColor = accentColor;
            document.querySelector(".audio-player").style.color = textColor;

            // ✅ Apply colors to Buttons
            document.querySelectorAll(".episode-actions .btn").forEach(btn => {
                btn.style.backgroundColor = highlightColor;
                btn.style.color = textColor;
            });

            // ✅ Apply colors to Footer
            document.querySelector("footer.section-darkgrey").style.backgroundColor = primaryColor;
            document.querySelector("footer.section-darkgrey").style.color = textColor;

            console.log("✅ Episode Page Theme Applied!");
        } catch (error) {
            console.error("❌ Error in Color Thief:", error);
        }
    };

    img.onerror = function () {
        console.error("❌ Error: Could not load the podcast logo.");
    };
}