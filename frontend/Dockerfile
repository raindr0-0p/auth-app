# Use Node.js 18-alpine image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the application for production
RUN npm run build

# Use a lightweight web server to serve the built app
FROM nginx:alpine
# Remove the default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf
# Copy our custom configuration
COPY nginx.conf /etc/nginx/conf.d
# Copy the built assets from the previous stage
COPY --from=0 /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]