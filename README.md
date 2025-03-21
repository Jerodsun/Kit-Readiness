# Kit Readiness

## Overview

The Kit Readiness tool is designed to streamline and optimize the process of assembling kits from various components stored across multiple warehouses. A comprehensive interface is provided to manage kits, components, and warehouse inventory. The readiness dashboard offers real-time insights into the number of kits that can be created against a benchmark. The interactive map visualization allows users to drill down into the material components available at each warehouse. The kit calculator determines the current kit assembly capacity at each location, and the rebalancing algorithm maximizes overall kit production by optimizing component transfers. The transfer and new product request features optimize the movement of products between warehouses with proper justification, ensuring a balanced and efficient inventory system.

<img src="docs/images/readiness_dashboard.png" alt="Example Readiness Dashboard" width="600">


## Environment Variables

Configure the application with a `.env` file to set environment variables.

1. Create a `.env` file in the root directory of your project:

   ```sh
   touch .env
   ```

2. Add your environment variables to the `.env` file. For example:

   ```env
   DEBUG=False
   ```

## Running the App with Docker

1. Build the Docker image:

   ```sh
   docker build -t kit-readiness .
   ```

2. Run the Docker container and pass the `.env` file:

   ```sh
   docker run --env-file .env -p 8050:8050 kit-readiness
   ```

3. Go to `http://localhost:8050` to see the app.
