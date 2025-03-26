import { IntervalResponse, Payload, SimulationRequestParams, VivariumDocument } from "./datamodel";
import { getTestDocument, getTestRequest } from "./test";

enum Runtimes {
  Local = "localhost",
  Production = "compose.biosimulations"
}



export class VivariumService {
  public endpointRoot!: string
  public localEndpointRoot = `http://localhost:8080`;
  
  constructor(endpointRoot?: string) {
    this.endpointRoot = endpointRoot ? endpointRoot : this.localEndpointRoot
  }

  public async submitSimulation(onData: (data: IntervalResponse) => void): Promise<void> {
    const requestParams: SimulationRequestParams = getTestRequest();

    const payload: Payload = this.formatPayload(requestParams);
    console.log(`Processing payload init: ${JSON.stringify(payload.init)} to\n${payload.url}`)
    const response = await fetch(payload.url, payload.init);
  
    if (!response.ok || !response.body) {
      console.error("❌ Failed to connect:", await response.text());
      return;
    } else {
      console.log(`Successfully subscribed to a response body:\n${response.status}`)
    }
  
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
  
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
  
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      console.log(`Buffer: ${buffer}`)
  
      for (const evt of events) {
        console.log(`Getting data event:\n${evt}`)
        if (evt.startsWith("data: ")) {
          const json = evt.slice("data: ".length).trim();
          try {
            const parsed = JSON.parse(json);
            onData(parsed);
          } catch (err) {
            console.warn("⚠️ Failed to parse JSON:", json);
          }
        }
      }
    }
}

public formatPayload(requestParams: SimulationRequestParams): Payload {
    const url: string = this.getSimulationUrl();
    const params = new URLSearchParams({ duration: requestParams.duration.toString() });
    return {
      url: `${url}?${params.toString()}`,
      init: {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestParams)
      }
    }
  }

  public static getRequestParams(duration: number, document: VivariumDocument): SimulationRequestParams {
    return {
      duration: duration,
      document: document
    }
  }

  public submitTestSimulation() {
    this.submitSimulation((data) => {
      console.log("Running simulate")
      const out = document.getElementById("output");
      if (out) {
        out.textContent += `\n📥 ${JSON.stringify(data, null, 2)}\n`;
      }
    });
  }

  private getSimulationUrl(): string {
    return `${this.endpointRoot}/simulate`
  }

}

async function streamEvents(
  job_name: string,
  duration: number,
  runtime: Runtimes.Local | Runtimes.Production = Runtimes.Local, 
  port: number = 8000
) {
  const doc = getTestDocument();
  const job_id = `simulation-${job_name}`;

  const url = new URL(`http://${runtime}:${port}/simulate`);
  url.searchParams.set("job_id", job_id);
  url.searchParams.set("duration", duration.toString());

  const response = await fetch(url.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(doc),
  });

  if (!response.ok || !response.body) {
    console.error("❌ Failed to connect:", await response.text());
    return;
  }

  const output = document.getElementById("output")!;
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      let eventType = "";
      let data = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          data += line.slice(6).trim();
        }
      }

      if (eventType === "intervalResponse") {
        try {
          const parsed: IntervalResponse = JSON.parse(data);
          renderBox(parsed);
        } catch (err) {
          console.warn("⚠️ Failed to parse JSON:", data);
        }
      }
    }
  }
}

function renderBox(data: IntervalResponse) {
  const output = document.getElementById("output")!;
  const box = document.createElement("div");
  box.className = "event-box";
  box.textContent = JSON.stringify(data.results, null, 2);
  output.appendChild(box);
}

streamEvents('test', 11);


// const service = new VivariumService();
// try {
//   await service.submitSimulation((data) => {
//     console.log(`Getting data: ${data}`)
//   });
//   console.log(`Done!`);
// } catch(err) {
//   console.log(`Error: ${err}`)
// }

  