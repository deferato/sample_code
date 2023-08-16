# Coding Sample

This repository has 2 sample codes that are part of some real work I have done on my day to day job
This is sanitised code, so many parts were removed for security reasons.

- A python bot to interact with Slack (used framework [errbot](https://github.com/errbotio/errbot))
    - cloudformation shows the yaml file to deploy the application
    - commands is where the commands the bot will accept are stored
    - _helpers are the helper functions for the commands

- AWS CDK project using Python to build a Remote Desktop Deployment on AWS
    - rdcb_stack deploys a full AWS CDK stack to install a Microsoft Connection broker
    - It uses a base image, then creates and ASG, with load balancer, and RDS SQL 
    - The userdata invokes a huge Powershell script to install and configure all services
    
