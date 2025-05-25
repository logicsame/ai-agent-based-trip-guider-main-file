# Tourist Spot Social Media - Deployment Guide

This guide provides instructions for deploying the Tourist Spot Social Media application in a production environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [MongoDB Setup](#mongodb-setup)
3. [Backend API Deployment](#backend-api-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Considerations](#security-considerations)
7. [Testing the Deployment](#testing-the-deployment)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the application, ensure you have the following:

- Python 3.8 or higher
- pip (Python package manager)
- Node.js 14 or higher (for frontend development)
- MongoDB (local installation or MongoDB Atlas account)
- Git

## MongoDB Setup

You have two options for MongoDB setup:

### Option 1: Local MongoDB Installation

1. **Install MongoDB** on your server:

   **Ubuntu/Debian:**
   ```bash
   # Import MongoDB public GPG key
   wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
   
   # Create list file for MongoDB
   echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
   
   # Update package database
   sudo apt-get update
   
   # Install MongoDB packages
   sudo apt-get install -y mongodb-org
   
   # Start MongoDB service
   sudo systemctl start mongod
   
   # Enable MongoDB service to start on boot
   sudo systemctl enable mongod
   ```

   **CentOS/RHEL:**
   ```bash
   # Create a .repo file for MongoDB
   sudo tee /etc/yum.repos.d/mongodb-org-6.0.repo << EOF
   [mongodb-org-6.0]
   name=MongoDB Repository
   baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/6.0/x86_64/
   gpgcheck=1
   enabled=1
   gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
   EOF
   
   # Install MongoDB packages
   sudo yum install -y mongodb-org
   
   # Start MongoDB service
   sudo systemctl start mongod
   
   # Enable MongoDB service to start on boot
   sudo systemctl enable mongod
   ```

2. **Configure MongoDB Security**:
   ```bash
   # Create admin user
   mongosh admin --eval "db.createUser({user: 'admin', pwd: 'secure_password', roles: ['root']})"
   
   # Edit MongoDB configuration file
   sudo nano /etc/mongod.conf
   ```

   Add the following to enable authentication:
   ```yaml
   security:
     authorization: enabled
   ```

   Restart MongoDB:
   ```bash
   sudo systemctl restart mongod
   ```

### Option 2: MongoDB Atlas (Cloud)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a new cluster (the free tier is sufficient for starting)
3. Create a database user with read/write permissions
4. Add your server's IP address to the IP Access List
5. Get your connection string by clicking 'Connect' > 'Connect your application'

## Backend API Deployment

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd ai-agent-based-trip-guider-main-file
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create uploads directory**:
   ```bash
   mkdir -p uploads/images uploads/videos
   chmod 755 uploads
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```
   # MongoDB Configuration
   MONGODB_URI=mongodb://username:password@localhost:27017/
   MONGODB_DB=tourist_social_db

   # JWT Authentication
   SECRET_KEY=your-secure-secret-key-for-jwt
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Application Settings
   UPLOAD_DIR=uploads
   ```

   For MongoDB Atlas, use the connection string provided:
   ```
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority
   ```

5. **Setup MongoDB**:
   ```bash
   python setup_mongodb.py
   ```

6. **Run the backend API with a production WSGI server**:
   
   Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

   Start the server:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

7. **Setup Nginx as a reverse proxy** (recommended for production):
   
   Install Nginx:
   ```bash
   sudo apt-get install nginx
   ```

   Create a configuration file:
   ```bash
   sudo nano /etc/nginx/sites-available/tourist-app
   ```

   Add the following configuration:
   ```
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /uploads {
           alias /path/to/your/project/uploads;
       }
   }
   ```

   Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/tourist-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

8. **Setup Systemd service** for automatic startup:
   ```bash
   sudo nano /etc/systemd/system/tourist-app.service
   ```

   Add the following:
   ```
   [Unit]
   Description=Tourist Spot Social Media API
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/your/project
   ExecStart=/usr/local/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   Restart=always
   StandardOutput=file:/var/log/tourist-app/access.log
   StandardError=file:/var/log/tourist-app/error.log

   [Install]
   WantedBy=multi-user.target
   ```

   Create log directory:
   ```bash
   sudo mkdir -p /var/log/tourist-app
   sudo chown ubuntu:ubuntu /var/log/tourist-app
   ```

   Enable and start the service:
   ```bash
   sudo systemctl enable tourist-app
   sudo systemctl start tourist-app
   ```

## Frontend Deployment

The Streamlit frontend can be deployed in several ways:

### Option 1: Direct Streamlit Deployment

1. **Install Streamlit**:
   ```bash
   pip install streamlit
   ```

2. **Run the Streamlit app**:
   ```bash
   streamlit run test_enhanced.py
   ```

3. **Setup Systemd service** for automatic startup:
   ```bash
   sudo nano /etc/systemd/system/tourist-frontend.service
   ```

   Add the following:
   ```
   [Unit]
   Description=Tourist Spot Social Media Frontend
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/your/project
   ExecStart=/usr/local/bin/streamlit run test_enhanced.py --server.port=8501
   Restart=always
   StandardOutput=file:/var/log/tourist-frontend/access.log
   StandardError=file:/var/log/tourist-frontend/error.log

   [Install]
   WantedBy=multi-user.target
   ```

   Create log directory:
   ```bash
   sudo mkdir -p /var/log/tourist-frontend
   sudo chown ubuntu:ubuntu /var/log/tourist-frontend
   ```

   Enable and start the service:
   ```bash
   sudo systemctl enable tourist-frontend
   sudo systemctl start tourist-frontend
   ```

### Option 2: Streamlit Cloud

1. Push your code to a GitHub repository
2. Sign up for [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Deploy the app with a few clicks

## Environment Configuration

For a production environment, update the following settings:

1. **Update `.env` file**:
   ```
   # MongoDB Configuration
   MONGODB_URI=your-production-mongodb-uri
   MONGODB_DB=tourist_social_db

   # JWT Authentication
   SECRET_KEY=your-very-secure-production-secret-key
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Application Settings
   UPLOAD_DIR=uploads
   ```

2. **Configure CORS** in `main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Update backend URL** in the Streamlit app:
   In `test_enhanced.py`, change:
   ```python
   BACKEND_URL = "https://api.yourdomain.com"
   ```

## Security Considerations

1. **Enable HTTPS**:
   Install Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Secure MongoDB**:
   - Use strong passwords
   - Enable authentication
   - Restrict network access
   - Regularly backup your database

3. **JWT Security**:
   - Use a strong, unique SECRET_KEY
   - Set reasonable token expiration times
   - Store tokens securely on the client side

4. **File Upload Security**:
   - Validate file types and sizes
   - Scan uploads for malware
   - Use secure file permissions

5. **Rate Limiting**:
   Add rate limiting to prevent abuse:
   ```python
   from fastapi.middleware.trustedhost import TrustedHostMiddleware
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.get("/api/endpoint")
   @limiter.limit("5/minute")
   async def rate_limited_endpoint(request: Request):
       return {"message": "This endpoint is rate limited"}
   ```

## Testing the Deployment

1. **Run the test suite**:
   ```bash
   cd tests
   python -m unittest discover
   ```

2. **Manual testing**:
   - Test user registration and login
   - Test tourist spot search
   - Test post creation and viewing
   - Test commenting and liking
   - Test media uploads

## Troubleshooting

### MongoDB Connection Issues

1. **Check MongoDB service**:
   ```bash
   sudo systemctl status mongod
   ```

2. **Check MongoDB logs**:
   ```bash
   sudo tail -f /var/log/mongodb/mongod.log
   ```

3. **Verify connection string**:
   For local MongoDB:
   ```
   mongodb://username:password@localhost:27017/tourist_social_db
   ```
   
   For MongoDB Atlas:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/tourist_social_db?retryWrites=true&w=majority
   ```

### API Server Issues

1. **Check API logs**:
   ```bash
   sudo tail -f /var/log/tourist-app/error.log
   ```

2. **Check Nginx logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Test API directly**:
   ```bash
   curl http://localhost:8000/health
   ```

### Frontend Issues

1. **Check Streamlit logs**:
   ```bash
   sudo tail -f /var/log/tourist-frontend/error.log
   ```

2. **Verify backend URL**:
   Ensure the BACKEND_URL in the Streamlit app is correct.

3. **Check browser console** for JavaScript errors.

## Conclusion

Your Tourist Spot Social Media application is now deployed and ready for use! Users can search for tourist spots, create posts with media, comment on posts, and interact with other travelers.

For any additional help or customization, refer to the source code documentation or contact the development team.
