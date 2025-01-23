# Team Leaderboard Dashboard

## Overview

A dynamic and interactive dashboard to display team rankings, achievements, and goals. Features include localization, dark mode, real-time data fetching, responsive design, and accessibility compliance.

## Features

- **Localization:** Supports multiple languages including English, Spanish, Arabic, German, French, and Chinese.
- **Dark Mode:** Toggle between light and dark themes.
- **Real-Time Data:** Fetches and displays real-time leaderboard data from the backend.
- **Responsive Design:** Optimized for all device sizes.
- **Accessibility:** Follows WCAG guidelines for accessibility.
- **Skeleton Loading:** Provides visual feedback while data is being fetched.

## Setup Instructions

### Prerequisites

- **AWS CLI:** Installed and configured with appropriate permissions.
- **SAM CLI:** Installed for backend deployment.
- **Node.js and npm:** Installed (if using build tools).
- **Git:** Installed for version control.

### Deployment

#### 1. **Backend Deployment**

Deploy the backend using AWS SAM.

```bash
cd infrastructure
./setup_deployment.sh
Ensure that the setup_deployment.sh script is executable and properly configured with your AWS credentials and desired configurations.

2. Frontend Deployment
Deploy the frontend to AWS S3 and invalidate the CloudFront cache.

bash
Copy
cd ../team-leaderboard-dashboard
./deployment_script.sh
Ensure that the deployment_script.sh has executable permissions and is correctly configured with your S3 bucket name and CloudFront Distribution ID.

Configuration
API Gateway URL:

Update the fetch URL in js/main.js with your deployed API Gateway URL.