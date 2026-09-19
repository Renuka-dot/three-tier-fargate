# 🚀 AWS 3-Tier Application Using ECS Fargate, RDS, ECR & GitHub Actions

This project demonstrates a simple **3-tier application deployed on AWS**.

The application uses:

- Frontend: HTML + JavaScript + Nginx
- Backend: Python + Flask
- Database: Amazon RDS MySQL
- Containers: Docker
- Container Registry: Amazon ECR
- Container Platform: Amazon ECS
- Compute: AWS Fargate
- Load Balancer: Application Load Balancer
- CI/CD: GitHub Actions
- Monitoring: Amazon CloudWatch
- Development/Admin Machine: Ubuntu
- AWS Management: AWS CLI

---

# 1. Architecture

```text
Developer
   |
   | git push
   v
GitHub Repository
   |
   v
GitHub Actions
   |
   | docker build
   | docker push
   v
Amazon ECR
   |
   v
Amazon ECS
   |
   v
AWS Fargate
   |
   +-----------------------+
   |                       |
Frontend Container     Backend Container
Nginx :80              Flask :5000
   |                       |
   +----------+------------+
              |
              v
        Amazon RDS
          MySQL
          :3306


User
 |
 v
Internet
 |
 v
Application Load Balancer
 |
 v
Frontend :80
 |
 v
Backend :5000
 |
 v
RDS MySQL :3306
```

---

# 2. Application Flow

The user accesses:

```text
http://<ALB-DNS-NAME>
```

Traffic flow:

```text
Browser
   ↓
Application Load Balancer
   ↓
Frontend - Nginx
   ↓
Backend - Python Flask
   ↓
Amazon RDS MySQL
```

The frontend contains a simple form.

The user enters a name:

```text
Chetan
```

and clicks:

```text
Add User
```

The frontend sends:

```text
POST /api/users
```

to the backend.

The backend stores the name in MySQL.

The frontend then calls:

```text
GET /api/users
```

and displays the users.

---

# 3. Create Ubuntu Machine

You can use:

- Ubuntu EC2 instance
- Local Ubuntu
- Ubuntu VM

For EC2, use approximately:

```text
AMI: Ubuntu 24.04
Instance Type: t3.micro / t3.small
Storage: 15-20 GB
```

Security Group:

```text
SSH
Port: 22
Source: My IP
```

Connect:

```bash
ssh -i mykey.pem ubuntu@<PUBLIC-IP>
```

Update Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
```

Install required packages:

```bash
sudo apt install -y \
git \
curl \
unzip \
docker.io \
python3 \
python3-pip \
python3-venv \
mysql-client
```

Enable Docker:

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

Add Ubuntu user to Docker group:

```bash
sudo usermod -aG docker ubuntu
```

Logout:

```bash
exit
```

Login again.

Verify:

```bash
docker --version
python3 --version
git --version
```

---

# 4. Install AWS CLI

Download:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
-o "awscliv2.zip"
```

Extract:

```bash
unzip awscliv2.zip
```

Install:

```bash
sudo ./aws/install
```

Verify:

```bash
aws --version
```

Configure AWS:

```bash
aws configure
```

Enter:

```text
AWS Access Key ID: <YOUR-ACCESS-KEY>

AWS Secret Access Key: <YOUR-SECRET-KEY>

Default region:
ap-south-1

Default output:
json
```

Verify AWS access:

```bash
aws sts get-caller-identity
```

Set variables:

```bash
export AWS_REGION=ap-south-1

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity \
--query Account \
--output text)
```

Check:

```bash
echo $AWS_REGION
echo $AWS_ACCOUNT_ID
```

---

# 5. Create Project

Go to home directory:

```bash
cd ~
```

Create project:

```bash
mkdir three-tier-fargate
cd three-tier-fargate
```

Create directories:

```bash
mkdir frontend backend
mkdir -p .github/workflows
```

Project structure:

```text
three-tier-fargate/
│
├── frontend/
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── task-definition.json
│
└── README.md
```

---

# 6. Create Backend

Go to backend:

```bash
cd ~/three-tier-fargate/backend
```

Create:

```bash
nano requirements.txt
```

Add:

```text
Flask==3.1.0
flask-cors==5.0.1
PyMySQL==1.1.1
gunicorn==23.0.0
```

Save:

```text
CTRL + O
ENTER
CTRL + X
```

---

# 7. Create Python Flask Backend

Create:

```bash
nano app.py
```

Add:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)

CORS(app)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "appdb")


def get_connection():

    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=5
    )


def initialize_database():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """)

        connection.commit()

    finally:

        connection.close()


@app.route("/api/health")
def health():

    return jsonify({
        "status": "UP"
    })


@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT id, name FROM users ORDER BY id DESC"
            )

            rows = cursor.fetchall()

            users = [
                {
                    "id": row[0],
                    "name": row[1]
                }
                for row in rows
            ]

            return jsonify(users)

    finally:

        connection.close()


@app.route("/api/users", methods=["POST"])
def add_user():

    data = request.get_json()

    name = data.get("name", "").strip()

    if not name:

        return jsonify({
            "error": "Name is required"
        }), 400

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                "INSERT INTO users(name) VALUES(%s)",
                (name,)
            )

        connection.commit()

        return jsonify({
            "message": "User added successfully"
        }), 201

    finally:

        connection.close()


if __name__ == "__main__":

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000
    )
```

Save.

Important:

```python
app.run(host="0.0.0.0", port=5000)
```

Backend will run on:

```text
5000
```

---

# 8. Create Backend Dockerfile

Inside:

```bash
cd ~/three-tier-fargate/backend
```

Create:

```bash
nano Dockerfile
```

Add:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
```

Backend flow:

```text
Python Image
    ↓
Create /app
    ↓
Install Flask/PyMySQL
    ↓
Copy app.py
    ↓
Expose 5000
    ↓
Start Flask
```

---

# 9. Create Frontend

Go to:

```bash
cd ~/three-tier-fargate/frontend
```

Create:

```bash
nano index.html
```

Add:

```html
<!DOCTYPE html>

<html>

<head>

<title>AWS Three Tier Application</title>

<style>

body {
    font-family: Arial;
    background: #f4f6f8;
    text-align: center;
    padding: 50px;
}

.container {
    background: white;
    max-width: 600px;
    margin: auto;
    padding: 30px;
    border-radius: 10px;
}

input {
    padding: 10px;
    width: 60%;
}

button {
    padding: 10px 20px;
    background: #ff9900;
    border: none;
    cursor: pointer;
}

li {
    list-style: none;
    margin: 10px;
}

</style>

</head>


<body>

<div class="container">

<h1>AWS Three Tier Application</h1>

<p>Frontend → Backend → RDS MySQL</p>

<input
id="name"
placeholder="Enter your name"
/>

<button onclick="addUser()">

Add User

</button>

<h2>Users</h2>

<ul id="users"></ul>

</div>


<script>

async function loadUsers() {

    const response =
        await fetch("/api/users");

    const users =
        await response.json();

    const list =
        document.getElementById("users");

    list.innerHTML = "";

    users.forEach(user => {

        const item =
            document.createElement("li");

        item.innerText =
            user.id + " - " + user.name;

        list.appendChild(item);

    });

}


async function addUser() {

    const name =
        document.getElementById("name").value;

    if (!name) {

        alert("Please enter a name");

        return;
    }

    await fetch("/api/users", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            name: name

        })

    });

    document.getElementById("name").value = "";

    loadUsers();

}


loadUsers();

</script>

</body>

</html>
```

---

# 10. Create Nginx Configuration

Create:

```bash
nano nginx.conf
```

Add:

```nginx
server {

    listen 80;

    server_name _;

    root /usr/share/nginx/html;

    index index.html;


    location / {

        try_files $uri $uri/ /index.html;

    }


    location /api/ {

        proxy_pass http://127.0.0.1:5000;

        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;

    }

}
```

Nginx works like:

```text
/
 ↓
index.html


/api/
 ↓
localhost:5000
 ↓
Flask
```

Frontend and backend will run in the **same ECS Fargate task**.

Therefore Nginx can reach backend using:

```text
127.0.0.1:5000
```

---

# 11. Create Frontend Dockerfile

Create:

```bash
nano Dockerfile
```

Add:

```dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

---

# 12. Verify Project

Run:

```bash
cd ~/three-tier-fargate

find .
```

Expected:

```text
.
./frontend
./frontend/index.html
./frontend/nginx.conf
./frontend/Dockerfile

./backend
./backend/app.py
./backend/requirements.txt
./backend/Dockerfile

./.github
./.github/workflows
```

---

# 13. Build Docker Images

Backend:

```bash
cd ~/three-tier-fargate

docker build \
-t three-tier-backend \
./backend
```

Frontend:

```bash
docker build \
-t three-tier-frontend \
./frontend
```

Check:

```bash
docker images
```

Expected:

```text
three-tier-frontend
three-tier-backend
```

---

# 14. Create Amazon ECR Repositories

Create backend ECR:

```bash
aws ecr create-repository \
--repository-name three-tier-backend \
--region $AWS_REGION
```

Create frontend ECR:

```bash
aws ecr create-repository \
--repository-name three-tier-frontend \
--region $AWS_REGION
```

Check:

```bash
aws ecr describe-repositories \
--region $AWS_REGION
```

---

# 15. Login Docker to ECR

Run:

```bash
aws ecr get-login-password \
--region $AWS_REGION \
| docker login \
--username AWS \
--password-stdin \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

Expected:

```text
Login Succeeded
```

---

# 16. Tag Docker Images

Frontend:

```bash
docker tag \
three-tier-frontend:latest \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/three-tier-frontend:latest
```

Backend:

```bash
docker tag \
three-tier-backend:latest \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/three-tier-backend:latest
```

---

# 17. Push Images to ECR

Frontend:

```bash
docker push \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/three-tier-frontend:latest
```

Backend:

```bash
docker push \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/three-tier-backend:latest
```

Verify frontend:

```bash
aws ecr list-images \
--repository-name three-tier-frontend
```

Verify backend:

```bash
aws ecr list-images \
--repository-name three-tier-backend
```

Flow:

```text
Source Code
    ↓
Docker Build
    ↓
Docker Images
    ↓
Amazon ECR
```

---

# 18. Create Amazon RDS MySQL

For the first project, create RDS from AWS Console.

Go to:

```text
AWS Console
    ↓
RDS
    ↓
Databases
    ↓
Create Database
```

Select:

```text
Creation Method:
Standard Create

Engine:
MySQL

Template:
Free Tier
or
Dev/Test

DB Identifier:
three-tier-db

Master Username:
admin

Master Password:
<YOUR-PASSWORD>
```

Example instance:

```text
db.t4g.micro
```

Storage:

```text
20 GB
```

For this lab:

```text
Public Access:
Yes
```

Create database.

Wait until:

```text
Status = Available
```

Copy the endpoint.

Example:

```text
three-tier-db.xxxxx.ap-south-1.rds.amazonaws.com
```

Do NOT add:

```text
:3306
```

to `DB_HOST`.

---

# 19. Configure RDS Security Group Temporarily

Find the RDS Security Group.

For initial testing, allow MySQL from your Ubuntu EC2 security group.

```text
Type:
MySQL/Aurora

Protocol:
TCP

Port:
3306

Source:
Ubuntu EC2 Security Group
```

Do NOT permanently allow:

```text
0.0.0.0/0
```

on port 3306.

---

# 20. Create Database

From Ubuntu:

```bash
mysql \
-h <RDS-ENDPOINT> \
-u admin \
-p
```

Enter password.

Create database:

```sql
CREATE DATABASE appdb;
```

Check:

```sql
SHOW DATABASES;
```

Expected:

```text
appdb
```

Exit:

```sql
exit;
```

The Python application automatically creates the:

```text
users
```

table.

---

# 21. Create ECS IAM Execution Role

Go to project:

```bash
cd ~/three-tier-fargate
```

Create trust policy:

```bash
cat > ecs-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",

  "Statement": [

    {

      "Effect": "Allow",

      "Principal": {

        "Service": "ecs-tasks.amazonaws.com"

      },

      "Action": "sts:AssumeRole"

    }

  ]

}
EOF
```

Create role:

```bash
aws iam create-role \
--role-name ecsTaskExecutionRole \
--assume-role-policy-document file://ecs-trust-policy.json
```

Attach ECS execution policy:

```bash
aws iam attach-role-policy \
--role-name ecsTaskExecutionRole \
--policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

Verify:

```bash
aws iam get-role \
--role-name ecsTaskExecutionRole
```

---

# 22. Create ECS Cluster

Run:

```bash
aws ecs create-cluster \
--cluster-name three-tier-cluster \
--region $AWS_REGION
```

Verify:

```bash
aws ecs describe-clusters \
--clusters three-tier-cluster
```

We are using:

```text
AWS ECS
+
AWS Fargate
```

No ECS EC2 worker nodes are required.

---

# 23. Create CloudWatch Log Groups

Frontend:

```bash
aws logs create-log-group \
--log-group-name /ecs/three-tier-frontend \
--region $AWS_REGION
```

Backend:

```bash
aws logs create-log-group \
--log-group-name /ecs/three-tier-backend \
--region $AWS_REGION
```

---

# 24. Create ECS Task Definition

Go to:

```bash
cd ~/three-tier-fargate
```

Create:

```bash
nano task-definition.json
```

Add:

```json
{
  "family": "three-tier-app",

  "networkMode": "awsvpc",

  "requiresCompatibilities": [
    "FARGATE"
  ],

  "cpu": "512",

  "memory": "1024",

  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",

  "containerDefinitions": [

    {

      "name": "frontend",

      "image": "ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/three-tier-frontend:latest",

      "essential": true,

      "portMappings": [

        {

          "containerPort": 80,

          "protocol": "tcp"

        }

      ],

      "logConfiguration": {

        "logDriver": "awslogs",

        "options": {

          "awslogs-group": "/ecs/three-tier-frontend",

          "awslogs-region": "ap-south-1",

          "awslogs-stream-prefix": "ecs"

        }

      }

    },

    {

      "name": "backend",

      "image": "ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/three-tier-backend:latest",

      "essential": true,

      "environment": [

        {

          "name": "DB_HOST",

          "value": "YOUR_RDS_ENDPOINT"

        },

        {

          "name": "DB_USER",

          "value": "admin"

        },

        {

          "name": "DB_PASSWORD",

          "value": "YOUR_DATABASE_PASSWORD"

        },

        {

          "name": "DB_NAME",

          "value": "appdb"

        }

      ],

      "portMappings": [

        {

          "containerPort": 5000,

          "protocol": "tcp"

        }

      ],

      "logConfiguration": {

        "logDriver": "awslogs",

        "options": {

          "awslogs-group": "/ecs/three-tier-backend",

          "awslogs-region": "ap-south-1",

          "awslogs-stream-prefix": "ecs"

        }

      }

    }

  ]

}
```

Replace:

```text
ACCOUNT_ID

YOUR_RDS_ENDPOINT

YOUR_DATABASE_PASSWORD
```

Automatically replace account ID:

```bash
sed -i "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-definition.json
```

Check:

```bash
cat task-definition.json
```

Register:

```bash
aws ecs register-task-definition \
--cli-input-json file://task-definition.json
```

Verify:

```bash
aws ecs list-task-definitions
```

> NOTE:
> For production, database passwords should be stored in AWS Secrets Manager rather than directly in the task definition.

---

# 25. Get Default VPC

Run:

```bash
export VPC_ID=$(aws ec2 describe-vpcs \
--filters Name=isDefault,Values=true \
--query 'Vpcs[0].VpcId' \
--output text)
```

Check:

```bash
echo $VPC_ID
```

---

# 26. Get Subnets

Run:

```bash
aws ec2 describe-subnets \
--filters Name=vpc-id,Values=$VPC_ID \
--query 'Subnets[*].[SubnetId,AvailabilityZone]' \
--output table
```

Choose two subnets from different Availability Zones.

Set:

```bash
export SUBNET1=subnet-xxxxxxxx
export SUBNET2=subnet-yyyyyyyy
```

Example only:

```text
SUBNET1 = ap-south-1a

SUBNET2 = ap-south-1b
```

Check:

```bash
echo $SUBNET1
echo $SUBNET2
```

---

# 27. Create ALB Security Group

Create:

```bash
export ALB_SG=$(aws ec2 create-security-group \
--group-name three-tier-alb-sg \
--description "Three tier ALB security group" \
--vpc-id $VPC_ID \
--query GroupId \
--output text)
```

Check:

```bash
echo $ALB_SG
```

Allow HTTP:

```bash
aws ec2 authorize-security-group-ingress \
--group-id $ALB_SG \
--protocol tcp \
--port 80 \
--cidr 0.0.0.0/0
```

---

# 28. Create ECS Security Group

Create:

```bash
export ECS_SG=$(aws ec2 create-security-group \
--group-name three-tier-ecs-sg \
--description "Three tier ECS security group" \
--vpc-id $VPC_ID \
--query GroupId \
--output text)
```

Check:

```bash
echo $ECS_SG
```

Allow ALB to access frontend:

```bash
aws ec2 authorize-security-group-ingress \
--group-id $ECS_SG \
--protocol tcp \
--port 80 \
--source-group $ALB_SG
```

Backend port 5000 does NOT need to be exposed publicly.

Communication:

```text
Nginx
 |
 | localhost:5000
 v
Flask
```

---

# 29. Configure RDS Security Group

Get RDS Security Group:

```bash
aws rds describe-db-instances \
--db-instance-identifier three-tier-db \
--query 'DBInstances[0].VpcSecurityGroups[*].VpcSecurityGroupId' \
--output text
```

Example:

```text
sg-0123456789
```

Set:

```bash
export RDS_SG=sg-0123456789
```

Allow ECS to access MySQL:

```bash
aws ec2 authorize-security-group-ingress \
--group-id $RDS_SG \
--protocol tcp \
--port 3306 \
--source-group $ECS_SG
```

Security flow:

```text
Internet
   |
   | 80
   v
ALB Security Group
   |
   | 80
   v
ECS Security Group
   |
   | 3306
   v
RDS Security Group
```

---

# 30. Create Application Load Balancer

Run:

```bash
aws elbv2 create-load-balancer \
--name three-tier-alb \
--subnets $SUBNET1 $SUBNET2 \
--security-groups $ALB_SG \
--scheme internet-facing \
--type application
```

Get ALB ARN:

```bash
export ALB_ARN=$(aws elbv2 describe-load-balancers \
--names three-tier-alb \
--query 'LoadBalancers[0].LoadBalancerArn' \
--output text)
```

Check:

```bash
echo $ALB_ARN
```

---

# 31. Create Target Group

Run:

```bash
aws elbv2 create-target-group \
--name three-tier-tg \
--protocol HTTP \
--port 80 \
--target-type ip \
--vpc-id $VPC_ID \
--health-check-path /
```

Important:

```text
Target Type = IP
```

because we are using Fargate with `awsvpc`.

Get Target Group ARN:

```bash
export TG_ARN=$(aws elbv2 describe-target-groups \
--names three-tier-tg \
--query 'TargetGroups[0].TargetGroupArn' \
--output text)
```

Check:

```bash
echo $TG_ARN
```

---

# 32. Create ALB Listener

Run:

```bash
aws elbv2 create-listener \
--load-balancer-arn $ALB_ARN \
--protocol HTTP \
--port 80 \
--default-actions Type=forward,TargetGroupArn=$TG_ARN
```

Traffic:

```text
Internet
   ↓
ALB :80
   ↓
Target Group :80
   ↓
Frontend Container :80
```

---

# 33. Create ECS Fargate Service

Run:

```bash
aws ecs create-service \
--cluster three-tier-cluster \
--service-name three-tier-service \
--task-definition three-tier-app \
--desired-count 1 \
--launch-type FARGATE \
--network-configuration "awsvpcConfiguration={subnets=[$SUBNET1,$SUBNET2],securityGroups=[$ECS_SG],assignPublicIp=ENABLED}" \
--load-balancers "targetGroupArn=$TG_ARN,containerName=frontend,containerPort=80"
```

Wait for service:

```bash
aws ecs wait services-stable \
--cluster three-tier-cluster \
--services three-tier-service
```

---

# 34. Check ECS Tasks

List tasks:

```bash
aws ecs list-tasks \
--cluster three-tier-cluster
```

Check service:

```bash
aws ecs describe-services \
--cluster three-tier-cluster \
--services three-tier-service \
--query 'services[0].[runningCount,pendingCount,desiredCount]' \
--output table
```

Expected:

```text
runningCount = 1

pendingCount = 0

desiredCount = 1
```

---

# 35. Check Target Health

Run:

```bash
aws elbv2 describe-target-health \
--target-group-arn $TG_ARN
```

You want:

```text
State:
healthy
```

---

# 36. Check Backend Logs

If application is failing:

```bash
aws logs tail \
/ecs/three-tier-backend \
--follow
```

Frontend:

```bash
aws logs tail \
/ecs/three-tier-frontend \
--follow
```

These commands are extremely useful for troubleshooting.

---

# 37. Get Application URL

Run:

```bash
aws elbv2 describe-load-balancers \
--names three-tier-alb \
--query 'LoadBalancers[0].DNSName' \
--output text
```

Example:

```text
three-tier-alb-123456789.ap-south-1.elb.amazonaws.com
```

Open:

```text
http://three-tier-alb-123456789.ap-south-1.elb.amazonaws.com
```

You should see:

```text
AWS Three Tier Application

Frontend → Backend → RDS MySQL

Enter your name

[ Add User ]

Users
```

Enter:

```text
Chetan
```

Click:

```text
Add User
```

Expected:

```text
1 - Chetan
```

---

# 38. Verify Complete Application Flow

When we click:

```text
Add User
```

the following happens:

```text
Browser
   ↓
POST /api/users
   ↓
ALB
   ↓
Nginx
   ↓
Flask
   ↓
INSERT INTO users
   ↓
RDS MySQL
```

When users are displayed:

```text
Browser
   ↓
GET /api/users
   ↓
ALB
   ↓
Nginx
   ↓
Flask
   ↓
SELECT FROM users
   ↓
RDS
   ↓
Flask JSON response
   ↓
Frontend
```

---

# 39. Create GitHub Repository

Create repository in GitHub:

```text
three-tier-fargate
```

Do NOT add README while creating it because we already have our project.

---

# 40. Create .gitignore

From Ubuntu:

```bash
cd ~/three-tier-fargate
```

Create:

```bash
nano .gitignore
```

Add:

```text
*.pem

.env

__pycache__/

ecs-trust-policy.json
```

IMPORTANT:

Never push:

```text
AWS Access Key

AWS Secret Key

Database passwords

.pem files
```

to GitHub.

---

# 41. Push Application to GitHub

Initialize Git:

```bash
git init
```

Set branch:

```bash
git branch -M main
```

Check:

```bash
git status
```

Add:

```bash
git add .
```

Commit:

```bash
git commit -m "Initial three tier application"
```

Connect repository:

```bash
git remote add origin \
https://github.com/YOUR_USERNAME/three-tier-fargate.git
```

Verify:

```bash
git remote -v
```

Push:

```bash
git push -u origin main
```

---

# 42. Configure GitHub Actions AWS Authentication

For this simple lab, create a dedicated IAM identity for GitHub Actions with permissions required for:

```text
ECR

ECS
```

Do NOT use the AWS root account.

For production, GitHub OIDC is recommended instead of storing long-lived AWS access keys.

For the quick lab, go to:

```text
GitHub Repository

Settings

↓

Secrets and variables

↓

Actions

↓

New repository secret
```

Create these secrets:

```text
AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

AWS_ACCOUNT_ID
```

Example:

```text
AWS_ACCOUNT_ID

123456789012
```

Never put these values directly into the YAML file.

---

# 43. Create GitHub Actions Pipeline

Go to:

```bash
cd ~/three-tier-fargate
```

Create:

```bash
mkdir -p .github/workflows
```

Create:

```bash
nano .github/workflows/deploy.yml
```

Add:

```yaml
name: Build and Deploy to ECS Fargate

on:

  push:

    branches:

      - main


env:

  AWS_REGION: ap-south-1

  ECS_CLUSTER: three-tier-cluster

  ECS_SERVICE: three-tier-service

  FRONTEND_REPOSITORY: three-tier-frontend

  BACKEND_REPOSITORY: three-tier-backend


jobs:

  deploy:

    runs-on: ubuntu-latest


    steps:


      - name: Checkout Source Code

        uses: actions/checkout@v4


      - name: Configure AWS Credentials

        uses: aws-actions/configure-aws-credentials@v6

        with:

          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}

          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

          aws-region: ${{ env.AWS_REGION }}


      - name: Login to Amazon ECR

        uses: aws-actions/amazon-ecr-login@v2


      - name: Build and Push Frontend

        run: |

          docker build \
            -t $FRONTEND_REPOSITORY \
            ./frontend

          docker tag \
            $FRONTEND_REPOSITORY:latest \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/$FRONTEND_REPOSITORY:latest

          docker push \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/$FRONTEND_REPOSITORY:latest


      - name: Build and Push Backend

        run: |

          docker build \
            -t $BACKEND_REPOSITORY \
            ./backend

          docker tag \
            $BACKEND_REPOSITORY:latest \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/$BACKEND_REPOSITORY:latest

          docker push \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/$BACKEND_REPOSITORY:latest


      - name: Deploy Application to ECS

        run: |

          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment


      - name: Wait for ECS Deployment

        run: |

          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE
```

Save.

---

# 44. Push GitHub Actions Pipeline

Run:

```bash
git add .
```

Commit:

```bash
git commit -m "Add GitHub Actions ECS deployment"
```

Push:

```bash
git push origin main
```

---

# 45. Check GitHub Actions

Open:

```text
GitHub Repository
      ↓
Actions
      ↓
Build and Deploy to ECS Fargate
```

Pipeline should perform:

```text
Checkout Code
      ↓
Configure AWS Credentials
      ↓
Login to ECR
      ↓
Build Frontend
      ↓
Push Frontend → ECR
      ↓
Build Backend
      ↓
Push Backend → ECR
      ↓
Update ECS Service
      ↓
Fargate starts new Task
```

---

# 46. Test CI/CD Pipeline

Modify frontend:

```bash
nano frontend/index.html
```

Change:

```html
<h1>AWS Three Tier Application</h1>
```

to:

```html
<h1>My AWS Fargate Project</h1>
```

Save.

Run:

```bash
git add .
```

Commit:

```bash
git commit -m "Update application frontend"
```

Push:

```bash
git push origin main
```

Now:

```text
git push
   ↓
GitHub
   ↓
GitHub Actions
   ↓
Docker Build
   ↓
ECR Push
   ↓
ECS Deployment
   ↓
Fargate
```

You don't manually run:

```text
docker build
docker push
aws ecs update-service
```

after this.

GitHub Actions does it automatically.

---

# 47. Verify Deployment

Check ECS:

```bash
aws ecs describe-services \
--cluster three-tier-cluster \
--services three-tier-service \
--query 'services[0].[runningCount,pendingCount,desiredCount]' \
--output table
```

Check target health:

```bash
aws elbv2 describe-target-health \
--target-group-arn $TG_ARN
```

Get ALB URL:

```bash
aws elbv2 describe-load-balancers \
--names three-tier-alb \
--query 'LoadBalancers[0].DNSName' \
--output text
```

Open the URL.

You should now see:

```text
My AWS Fargate Project
```

---

# 48. Final Architecture

```text
                         DEVELOPER
                             |
                             |
                          git push
                             |
                             v
                         GITHUB
                             |
                             v
                      GITHUB ACTIONS
                             |
                +------------+------------+
                |                         |
                v                         v
        Build Frontend             Build Backend
        Docker Image               Docker Image
                |                         |
                +------------+------------+
                             |
                             v
                        AMAZON ECR
                             |
                             v
                         AMAZON ECS
                             |
                             v
                       AWS FARGATE
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
             FRONTEND                 BACKEND
              NGINX                    FLASK
               :80                     :5000
                 |                       |
                 +-----------+-----------+
                             |
                             v
                       AMAZON RDS
                          MYSQL
                          :3306


USER
 |
 |
 v
INTERNET
 |
 |
 v
APPLICATION LOAD BALANCER
 |
 |
 v
FRONTEND :80
 |
 |
 v
BACKEND :5000
 |
 |
 v
RDS MYSQL :3306
```

---

# 49. AWS Resources Used

| Layer | Technology |
|---|---|
| Frontend | HTML + JavaScript |
| Web Server | Nginx |
| Backend | Python Flask |
| Database | Amazon RDS MySQL |
| Container | Docker |
| Registry | Amazon ECR |
| Orchestration | Amazon ECS |
| Compute | AWS Fargate |
| Load Balancing | Application Load Balancer |
| Networking | VPC + Subnets |
| Security | Security Groups |
| IAM | ECS Execution Role |
| Logging | CloudWatch Logs |
| CI/CD | GitHub Actions |
| Source Control | GitHub |
| Management | AWS CLI |

---

# 50. Security Group Flow

## ALB Security Group

Inbound:

```text
HTTP
Port 80
Source 0.0.0.0/0
```

## ECS Security Group

Inbound:

```text
HTTP
Port 80
Source = ALB Security Group
```

## RDS Security Group

Inbound:

```text
MySQL
Port 3306
Source = ECS Security Group
```

Therefore:

```text
Internet
   |
   | 80
   v
ALB
   |
   | 80
   v
ECS Fargate
   |
   | 3306
   v
RDS
```

Port `5000` does not need public access because frontend and backend containers are inside the same ECS task.

---

# 51. Important Ports

| Component | Port |
|---|---:|
| ALB | 80 |
| Nginx Frontend | 80 |
| Flask Backend | 5000 |
| MySQL | 3306 |

---

# 52. Important Troubleshooting Commands

## Check AWS Login

```bash
aws sts get-caller-identity
```

## Check Docker Images

```bash
docker images
```

## Check ECR Images

```bash
aws ecr list-images \
--repository-name three-tier-frontend
```

```bash
aws ecr list-images \
--repository-name three-tier-backend
```

## Check ECS Cluster

```bash
aws ecs describe-clusters \
--clusters three-tier-cluster
```

## Check ECS Service

```bash
aws ecs describe-services \
--cluster three-tier-cluster \
--services three-tier-service
```

## Check Running Tasks

```bash
aws ecs list-tasks \
--cluster three-tier-cluster
```

## Check Target Health

```bash
aws elbv2 describe-target-health \
--target-group-arn $TG_ARN
```

## Check Backend Logs

```bash
aws logs tail \
/ecs/three-tier-backend \
--follow
```

## Check Frontend Logs

```bash
aws logs tail \
/ecs/three-tier-frontend \
--follow
```

---

# 53. If ECS Task Is Stopping

Get stopped tasks:

```bash
aws ecs list-tasks \
--cluster three-tier-cluster \
--desired-status STOPPED
```

Copy task ARN.

Then:

```bash
aws ecs describe-tasks \
--cluster three-tier-cluster \
--tasks <TASK-ARN>
```

Look for:

```text
stoppedReason

exitCode

reason
```

Then check CloudWatch logs.

---

# 54. If ALB Shows 502

Check:

```bash
aws elbv2 describe-target-health \
--target-group-arn $TG_ARN
```

Check frontend logs:

```bash
aws logs tail \
/ecs/three-tier-frontend \
--follow
```

Check backend logs:

```bash
aws logs tail \
/ecs/three-tier-backend \
--follow
```

Verify backend is listening:

```text
0.0.0.0:5000
```

and Nginx contains:

```nginx
proxy_pass http://127.0.0.1:5000;
```

---

# 55. If Database Connection Fails

Verify:

```text
DB_HOST
DB_USER
DB_PASSWORD
DB_NAME
```

Check that:

```text
DB_HOST = RDS endpoint
```

NOT:

```text
http://RDS-ENDPOINT
```

and NOT:

```text
RDS-ENDPOINT:3306
```

Example:

```text
three-tier-db.xxxxxx.ap-south-1.rds.amazonaws.com
```

Check RDS security group:

```text
TCP 3306

Source:
ECS Security Group
```

---

# 56. Simple Interview Explanation

## Frontend

> The frontend is a simple HTML and JavaScript application served through an Nginx container running on port 80.

## Backend

> The backend is a Python Flask REST API running on port 5000. It provides GET and POST APIs for retrieving and creating users.

## Database

> Amazon RDS MySQL is used as the database layer. The Flask backend connects to RDS and stores user information.

## Docker

> The frontend and backend applications have separate Dockerfiles and are built as separate Docker images.

## ECR

> Amazon ECR stores the frontend and backend Docker images.

## ECS

> Amazon ECS manages the container deployment.

## Fargate

> AWS Fargate runs the ECS tasks without requiring us to manage EC2 worker instances.

## ALB

> An internet-facing Application Load Balancer exposes the application to users and forwards traffic to the frontend container.

## GitHub Actions

> GitHub Actions provides CI/CD. Whenever code is pushed to the main branch, the pipeline builds new Docker images, pushes them to ECR and triggers a new ECS deployment.

## RDS

> The application data is stored separately in Amazon RDS, so application data remains persistent even when Fargate tasks are replaced.

---

# 57. CI/CD Flow

```text
Developer changes code
        ↓
git add .
        ↓
git commit
        ↓
git push
        ↓
GitHub
        ↓
GitHub Actions starts
        ↓
Checkout source
        ↓
Authenticate with AWS
        ↓
Docker build frontend
        ↓
Docker build backend
        ↓
Push frontend → ECR
        ↓
Push backend → ECR
        ↓
Update ECS Service
        ↓
Old Fargate task replaced
        ↓
New containers pull images from ECR
        ↓
ALB health check succeeds
        ↓
Application becomes available
```

---

# 58. Complete Project Flow in One Line

```text
GitHub
→ GitHub Actions
→ Docker Build
→ Amazon ECR
→ Amazon ECS
→ AWS Fargate
→ ALB
→ Nginx Frontend
→ Flask Backend
→ Amazon RDS MySQL
```

---

# 59. Project Summary

This project demonstrates how to deploy a containerized three-tier web application on AWS.

The frontend is served using Nginx.

The backend is implemented using Python Flask.

The database is Amazon RDS MySQL.

Docker is used to containerize the frontend and backend.

Amazon ECR stores Docker images.

Amazon ECS manages container deployments.

AWS Fargate provides serverless container compute.

Application Load Balancer exposes the application to the internet.

CloudWatch stores application logs.

GitHub stores source code.

GitHub Actions automatically builds, pushes and deploys new versions of the application.

The complete deployment flow is:

```text
Code
 ↓
GitHub
 ↓
GitHub Actions
 ↓
Docker
 ↓
ECR
 ↓
ECS
 ↓
Fargate
 ↓
ALB
 ↓
Frontend
 ↓
Backend
 ↓
RDS
```

---

# 60. Cleanup After Practice

AWS resources can generate charges.

After completing the project, delete resources you no longer need.

Delete ECS service:

```bash
aws ecs update-service \
--cluster three-tier-cluster \
--service three-tier-service \
--desired-count 0
```

Then:

```bash
aws ecs delete-service \
--cluster three-tier-cluster \
--service three-tier-service
```

Delete ECS cluster:

```bash
aws ecs delete-cluster \
--cluster three-tier-cluster
```

Delete ALB:

```bash
aws elbv2 delete-load-balancer \
--load-balancer-arn $ALB_ARN
```

Delete target group after the ALB is deleted:

```bash
aws elbv2 delete-target-group \
--target-group-arn $TG_ARN
```

Delete ECR repositories:

```bash
aws ecr delete-repository \
--repository-name three-tier-frontend \
--force
```

```bash
aws ecr delete-repository \
--repository-name three-tier-backend \
--force
```

Delete RDS when you are completely finished:

```bash
aws rds delete-db-instance \
--db-instance-identifier three-tier-db \
--skip-final-snapshot
```

Only run the cleanup commands when you no longer need the project.

---

# 🎯 Final Result

After completing this project, you have practically implemented:

**Ubuntu + Git + GitHub + Docker + HTML + JavaScript + Nginx + Python + Flask + REST API + MySQL + Amazon RDS + Amazon ECR + Amazon ECS + AWS Fargate + ALB + VPC + Security Groups + IAM + CloudWatch + AWS CLI + GitHub Actions + CI/CD**

This is a complete AWS container-based 3-tier application project.
