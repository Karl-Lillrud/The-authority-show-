const express = require("express");
const bodyParser = require("body-parser");
const path = require("path");
const multer = require("multer");
const { DynamoDBClient, PutItemCommand } = require("@aws-sdk/client-dynamodb");
const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");

const REGION = "eu-north-1";
const TABLE_NAME = "Guests";
const S3_BUCKET = "my-profile-photo";

const app = express();
const dynamoDbClient = new DynamoDBClient({ region: REGION });
const s3Client = new S3Client({ region: REGION });

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname)));

// Function to upload file to S3
const uploadToS3 = async (fileBuffer, fileName, mimeType) => {
    const command = new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: `profile-photo/${Date.now()}-${fileName}`,
        Body: fileBuffer,
        ContentType: mimeType,
    });

    try {
        await s3Client.send(command);
        console.log(`File uploaded successfully to ${S3_BUCKET}`);
        return `https://${S3_BUCKET}.s3.${REGION}.amazonaws.com/profile-photo/${Date.now()}-${fileName}`;
    } catch (error) {
        console.error("Error uploading to S3:", error);
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
        profilePhotoUrl = await uploadToS3(req.file.buffer, req.file.originalname, req.file.mimetype);
    } catch (error) {
        return res.status(500).send("Failed to upload profile photo. Please try again later.");
    }

    const item = {
        guestId: { S: `guest-${Date.now()}` },
        firstName: { S: firstName },
        lastName: { S: lastName },
        company: { S: company },
        email: { S: email },
        whatsapp: { S: whatsapp },
        linkedin: { S: linkedin || "Not Provided" },
        instagram: { S: instagram || "Not Provided" },
        tiktok: { S: tiktok || "Not Provided" },
        twitter: { S: twitter || "Not Provided" },
        bio: { S: bio || "" },
        areas: { S: areas || "" },
        guest1Email: { S: guest1Email || "" },
        guest1Name: { S: guest1Name || "" },
        guest2Email: { S: guest2Email || "" },
        guest2Name: { S: guest2Name || "" },
        guest3Name: { S: guest3Name || "" },
        connectWithKarl: { S: connectWithKarl || "Not Provided" },
        profilePhoto: { S: profilePhotoUrl },
        createdAt: { S: new Date().toISOString() },
    };

    try {
        const command = new PutItemCommand({ TableName: TABLE_NAME, Item: item });
        await dynamoDbClient.send(command);

        res.status(200).json({ redirectUrl: "https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1StAWY3QkvWg4Bd7AwjUX2FSsWBLNZ0Lo5-nILIiHj83z-768h9AC5qew89s8XHq9gzuHa62NV" });
    } catch (error) {
        console.error("Error inserting into DynamoDB:", error);
        res.status(500).send("Could not save data to DynamoDB.");
    }
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
