# Use an official Node runtime as the parent image
FROM node:18 as build-deps

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the current directory contents into the container at /app
COPY . ./

# Build the app
RUN npm run build

# Use nginx to serve the built app
FROM nginx:1.19.0-alpine
COPY --from=build-deps /app/build /usr/share/nginx/html

# Informs Docker that the container listens on the specified network port at runtime.
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]

