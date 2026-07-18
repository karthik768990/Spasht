FROM node:18-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose Vite's default port
EXPOSE 5173

# Start the dev server
CMD ["npm", "run", "dev", "--", "--host"]
