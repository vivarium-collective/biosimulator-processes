class VivariumService {
    constructor(url = "http://127.0.0.1:8080/events") {
        this.url = url;
        this.eventSource = new EventSource(this.url);

        this.eventSource.onerror = (error) => {
            console.error("SSE Error:", error);
        };

        this.eventSource.onmessage = (event) => {
            console.log("Received event:", event);
        };
    }

    listen() {
        this.eventSource.addEventListener("mem", (event) => {
            try {
                const data = JSON.parse(event.data);
                document.getElementById("mem-total").textContent = (data.total / 1_000_000).toFixed(2);
                document.getElementById("mem-used").textContent = (data.used / 1_000_000).toFixed(2);
                document.getElementById("mem-percent").textContent = data.used_percent.toFixed(2);
            } catch (e) {
                console.error("Error parsing memory data:", e);
            }
        });

        this.eventSource.addEventListener("cpu", (event) => {
            try {
                const data = JSON.parse(event.data);
                document.getElementById("cpu-user").textContent = data.user.toFixed(2);
                document.getElementById("cpu-system").textContent = data.system.toFixed(2);
                document.getElementById("cpu-idle").textContent = data.idle.toFixed(2);
            } catch (e) {
                console.error("Error parsing CPU data:", e);
            }
        });
    }
}