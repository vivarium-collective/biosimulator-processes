import { IntervalResponse, Payload, SimulationRequestParams, VivariumDocument } from "./datamodel";
import { getTestDocument, getTestRequest } from "./test";

enum Runtimes {
  Local = "localhost",
  Production = "compose.biosimulations"
}

const testDoc = {
  "state": {
      "membrane": {
          "_type": "process",
          "address": "local:simple-membrane-process",
          "config": {
              "characteristic_time_step": 1,
              "geometry": {
                  "type": "icosphere",
                  "parameters": {
                      "radius": 1,
                      "subdivision": 2
                  }
              },
              "tension_model": {
                  "modulus": 0.1,
                  "preferred_area": 12.4866
              },
              "osmotic_model": {
                  "preferred_volume": 2.9306666666666668,
                  "reservoir_volume": 1,
                  "strength": 0.02,
                  "volume": 2.9
              },
              "parameters": {
                  "bending": {
                      "Kbc": 0.0000822
                  },
                  "damping": 0.05
              },
              "tolerance": 1e-11,
              "console_output": false
          },
          "inputs": {
              "geometry": [
                  "geometry_store"
              ],
              "velocities": [
                  "velocities_store"
              ],
              "protein_density": [
                  "protein_density_store"
              ],
              "volume": [
                  "volume_store"
              ],
              "preferred_volume": [
                  "preferred_volume_store"
              ],
              "reservoir_volume": [
                  "reservoir_volume_store"
              ],
              "surface_area": [
                  "surface_area_store"
              ],
              "osmotic_strength": [
                  "osmotic_strength_store"
              ]
          },
          "outputs": {
              "geometry": [
                  "geometry_store"
              ],
              "velocities": [
                  "velocities_store"
              ],
              "protein_density": [
                  "protein_density_store"
              ],
              "volume": [
                  "volume_store"
              ],
              "preferred_volume": [
                  "preferred_volume_store"
              ],
              "reservoir_volume": [
                  "reservoir_volume_store"
              ],
              "surface_area": [
                  "surface_area_store"
              ],
              "net_forces": [
                  "net_forces_store"
              ]
          }
      },
      "emitter": {
          "_type": "step",
          "address": "local:ram-emitter",
          "config": {
              "emit": {
                  "geometry": "GeometryType",
                  "velocities": "VelocitiesType",
                  "protein_density": "ProteinDensityType",
                  "volume": "float",
                  "preferred_volume": "float",
                  "reservoir_volume": "float",
                  "surface_area": "float",
                  "net_forces": "MechanicalForcesType",
                  "notable_vertices": "list[boolean]"
              }
          },
          "inputs": {
              "geometry": [
                  "geometry_store"
              ],
              "velocities": [
                  "velocities_store"
              ],
              "protein_density": [
                  "protein_density_store"
              ],
              "volume": [
                  "volume_store"
              ],
              "preferred_volume": [
                  "preferred_volume_store"
              ],
              "reservoir_volume": [
                  "reservoir_volume_store"
              ],
              "surface_area": [
                  "surface_area_store"
              ],
              "net_forces": [
                  "net_forces_store"
              ]
          }
      }
  }
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
      console.error("Failed to connect:", await response.text());
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
  const doc = testDoc;  // getTestDocument();
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
  
  // Create a container for the event
  const container = document.createElement("div");
  container.className = "event-container";

  // Heading for the event
  const heading = document.createElement("h1");
  heading.className = "event-heading";
  heading.textContent = `Time: ${data.interval_id}`;
  container.appendChild(heading);

  // Box with interval data
  const box = document.createElement("div");
  box.className = "event-box";
  const vertexData = data.results.geometry.vertices;
  const intervalData = vertexData[vertexData.length - 1];
  box.textContent = JSON.stringify(intervalData, null, 2);
  container.appendChild(box);

  // Append to output
  output.appendChild(container);
}


streamEvents('test', 11);


export async function testSimulationSSE() {
  const requestBody = {
    document: {
      state: {
        global_time: "0.0",
        Tx: {
          inputs: {
            DNA: ["DNA"],
            mRNA: ["mRNA"]
          },
          outputs: {
            DNA: ["DNA"],
            mRNA: ["mRNA"],
            dC: ["dC"]
          },
          interval: 1.0,
          address: "local:tx",
          config: {
            ktsc: "22.2",
            kdeg: "-0.11",
            k: "0.001"
          }
        },
        DNA: "10",
        mRNA: "100.0",
        dC: "0",
        emitter: {
          address: "local:ram-emitter",
          config: {
            emit: {
              global_time: "any",
              DNA: "any",
              mRNA: "any",
              dC: "any"
            }
          },
          inputs: {
            global_time: ["global_time"],
            DNA: ["DNA"],
            mRNA: ["mRNA"],
            dC: ["dC"]
          },
          outputs: null
        }
      },
      composition:
        "(global_time:float|Tx:process[(DNA:float|mRNA:float),(DNA:float|mRNA:float|dC:float)]|DNA:float|mRNA:float|dC:float|emitter:step[(global_time:any|DNA:any|mRNA:any|dC:any),()])"
    },
    duration: 5
  };

  const response = await fetch("http://localhost:8080/simulate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok || !response.body) {
    console.error("❌ Simulation request failed");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const chunk of parts) {
      if (chunk.startsWith("data: ")) {
        const jsonStr = chunk.slice("data: ".length).trim();
        try {
          const data = JSON.parse(jsonStr);
          console.log("📥 Interval Data:", data);
        } catch (err) {
          console.warn("⚠️ Could not parse chunk:", jsonStr);
        }
      }
    }
  }

  console.log("✅ Stream finished");
}

// testSimulationSSE();


  