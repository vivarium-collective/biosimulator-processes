// init-mongo.js

print(">>> Initializing MongoDB Replica Set...");

try {
    rs.initiate({
        _id: "rs0",
        members: [{ _id: 0, host: "mongo:27017", priority: 1 }]
    });

    print(">>> Replica Set Initialized!");
} catch (e) {
    print(">>> Replica Set Already Initialized, skipping...");
}

// Check status
printjson(rs.status());
