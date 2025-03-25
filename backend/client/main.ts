type SimulationDocument = Record<string, any>;
  
  type SimulationRequest = {
    duration: number;
    document: SimulationDocument;
};
  
  type SimulationResponse = {
    job_id: string;
    timestamp: string;
    status: string;
    results: Record<string, any>;
    interval_id?: number;
};
  
const testDocument: SimulationDocument = {
    "state": {
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
    "composition":
      "(global_time:float|Tx:process[(DNA:float|mRNA:float),(DNA:float|mRNA:float|dC:float)]|DNA:float|mRNA:float|dC:float|emitter:step[(global_time:any|DNA:any|mRNA:any|dC:any),()])"
  };
  
async function simulate(onData: (data: SimulationResponse) => void): Promise<void> {
    const requestParams: SimulationRequest = {
      duration: 5,
      document: testDocument
    };
    console.log(`Running simulate with: ${JSON.stringify(requestParams)}`)
  
    const response = await fetch("http://localhost:8080/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestParams)
    });
  
    if (!response.ok || !response.body) {
      console.error("❌ Failed to connect:", await response.text());
      return;
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
  
      for (const evt of events) {
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
  
simulate((data) => {
    console.log("Running simulate")
    const out = document.getElementById("output");
    if (out) {
      out.textContent += `\n📥 ${JSON.stringify(data, null, 2)}\n`;
    }
  });
  