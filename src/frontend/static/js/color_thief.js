document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Color Thief Debug Started");

    if (typeof ColorThief === "undefined") {
        console.error("❌ Error: ColorThief library failed to load.");
        return;
    }

    const logoImg = document.getElementById("podcast-logo");

    if (!logoImg || !logoImg.src) {
        console.error("❌ Error: No valid podcast logo found!");
        return;
    }

    console.log("✅ Logo image found, source:", logoImg.src);

    let img = new Image();
    img.crossOrigin = "Anonymous";

    // If it's a Base64 image, load it properly
    if (logoImg.src.startsWith("data:image")) {
        img.src = logoImg.src;
    } else {
        img.src = logoImg.src;
    }

    img.onload = function () {
        console.log("✅ Image successfully loaded:", img.src);
        try {
            const colorThief = new ColorThief();
            const palette = colorThief.getPalette(img, 3);

            if (!palette || palette.length < 3) {
                console.error("❌ Error: No colors extracted.");
                return;
            }

            console.log("🎨 Extracted Colors:", palette);

            document.body.style.background = `linear-gradient(to right, 
                rgb(${palette[0].join(",")}), 
                rgb(${palette[1].join(",")}), 
                rgb(${palette[2].join(",")})
            )`;

            console.log("✅ Background updated successfully!");
        } catch (error) {
            console.error("❌ Error in Color Thief:", error);
        }
    };

    img.onerror = function () {
        console.error("❌ Error: Could not load the podcast logo.");
    };
});
