import { IntervalResponse, Payload, SimulationRequestParams, VivariumDocument } from "./datamodel";
import { getTestRequest } from "./test";

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

const service = new VivariumService();
try {
  await service.submitSimulation((data) => {
    console.log(`Getting data: ${data}`)
  });
  console.log(`Done!`);
} catch(err) {
  console.log(`Error: ${err}`)
}

  