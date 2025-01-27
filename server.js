// Import required modules
const express = require("express");
const bodyParser = require("body-parser");
const path = require("path");
const multer = require("multer");
const { BlobServiceClient } = require("@azure/storage-blob");
const { CosmosClient } = require("@azure/cosmos");

// Azure configuration
const AZURE_STORAGE_CONNECTION_STRING = "<YOUR_AZURE_STORAGE_CONNECTION_STRING>";
const COSMOS_DB_ENDPOINT = "https://cosmosdbservice.documents.azure.com:443/;AccountKey=K9RahnO3WSXA6P1UaWu4RJOLmSwXweeVFqTrt6L6JBvVfFoMGRG4VaxqzzMcDEJTYuJ8P32Og0KbACDbOaVVLg==;";
const COSMOS_DB_KEY = "K9RahnO3WSXA6P1UaWu4RJOLmSwXweeVFqTrt6L6JBvVfFoMGRG4VaxqzzMcDEJTYuJ8P32Og0KbACDbOaVVLg";
const DATABASE_ID = "PodcastManagement";
const CONTAINER_ID = "Guests";

const app = express();
const blobServiceClient = BlobServiceClient.fromConnectionString(AZURE_STORAGE_CONNECTION_STRING);
const cosmosClient = new CosmosClient({ endpoint: COSMOS_DB_ENDPOINT, key: COSMOS_DB_KEY });
const database = cosmosClient.database(DATABASE_ID);
const container = database.container(CONTAINER_ID);

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname)));

// Function to upload file to Azure Blob Storage
const uploadToAzureBlob = async (fileBuffer, fileName) => {
    const containerClient = blobServiceClient.getContainerClient("profile-photos");
    const blobName = `profile-photo/${Date.now()}-${fileName}`;
    const blockBlobClient = containerClient.getBlockBlobClient(blobName);

    try {
        await blockBlobClient.upload(fileBuffer, fileBuffer.length);
        console.log(`File uploaded successfully to Azure Blob Storage: ${blobName}`);
        return blockBlobClient.url;
    } catch (error) {
        console.error("Error uploading to Azure Blob Storage:", error);
        throw error;
    }
};

// Route for handling form submissions
app.post("/submit", upload.single("profilePhoto"), async (req, res) => {
    const {
        firstName,
        lastName,
        company,
        email,
        whatsapp,
        linkedin,
        instagram,
        tiktok,
        twitter,
        bio,
        areas,
        guest1Email,
        guest1Name,
        guest2Email,
        guest2Name,
        guest3Name,
        connectWithKarl,
    } = req.body;

    if (!firstName || !lastName || !company || !email || !whatsapp || !req.file) {
        return res.status(400).send("All required fields, including profile photo, must be filled!");
    }

    let profilePhotoUrl = "";
    try {
        profilePhotoUrl = await uploadToAzureBlob(req.file.buffer, req.file.originalname);
    } catch (error) {
        return res.status(500).send("Failed to upload profile photo. Please try again later.");
    }

    const item = {
        id: `guest-${Date.now()}`,
        firstName,
        lastName,
        company,
        email,
        whatsapp,
        linkedin: linkedin || "Not Provided",
        instagram: instagram || "Not Provided",
        tiktok: tiktok || "Not Provided",
        twitter: twitter || "Not Provided",
        bio: bio || "",
        areas: areas || "",
        guest1Email: guest1Email || "",
        guest1Name: guest1Name || "",
        guest2Email: guest2Email || "",
        guest2Name: guest2Name || "",
        guest3Name: guest3Name || "",
        connectWithKarl: connectWithKarl || "Not Provided",
        profilePhoto: profilePhotoUrl,
        createdAt: new Date().toISOString(),
    };

    try {
        await container.items.create(item);
        res.status(200).json({ redirectUrl: "https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1StAWY3QkvWg4Bd7AwjUX2FSsWBLNZ0Lo5-nILIiHj83z-768h9AC5qew89s8XHq9gzuHa62NV" });
    } catch (error) {
        console.error("Error inserting into Cosmos DB:", error);
        res.status(500).send("Could not save data to Cosmos DB.");
    }
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
