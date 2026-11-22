const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// Store notifications in memory for local testing
let notifications = [];

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve frontend files
app.use(express.static(path.join(__dirname, "static")));

// Homepage
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "static", "index.html"));
});

// Notifications page
app.get("/notify", (req, res) => {
    res.sendFile(path.join(__dirname, "static", "notify.html"));
});

// Health check
app.get("/api/health", (req, res) => {
    res.json({
        success: true,
        message: "CloudNotify server is running",
        status: "healthy"
    });
});

// Send notification
app.post("/notify", (req, res) => {
    const { title, message } = req.body;

    if (
        typeof title !== "string" ||
        typeof message !== "string" ||
        !title.trim() ||
        !message.trim()
    ) {
        return res.status(400).json({
            success: false,
            message: "Title and message are required"
        });
    }

    const notification = {
        id: Date.now().toString(),
        title: title.trim(),
        message: message.trim(),
        createdAt: new Date().toISOString(),
        read: false
    };

    notifications.unshift(notification);

    res.status(201).json({
        success: true,
        message: "Notification sent successfully!",
        notification
    });
});

// Get all notifications
app.get("/api/notifications", (req, res) => {
    res.json({
        success: true,
        notifications
    });
});

// Mark notification as read
app.patch("/api/notifications/:id/read", (req, res) => {
    const notification = notifications.find(
        item => item.id === req.params.id
    );

    if (!notification) {
        return res.status(404).json({
            success: false,
            message: "Notification not found"
        });
    }

    notification.read = true;

    res.json({
        success: true,
        message: "Notification marked as read",
        notification
    });
});

// Delete notification
app.delete("/api/notifications/:id", (req, res) => {
    const oldLength = notifications.length;

    notifications = notifications.filter(
        item => item.id !== req.params.id
    );

    if (notifications.length === oldLength) {
        return res.status(404).json({
            success: false,
            message: "Notification not found"
        });
    }

    res.json({
        success: true,
        message: "Notification deleted successfully"
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`CloudNotify server running on port ${PORT}`);
});