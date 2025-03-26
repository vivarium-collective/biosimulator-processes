export const getTestDocument = () => {
  return {
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
    composition: "(global_time:float|Tx:process[(DNA:float|mRNA:float),(DNA:float|mRNA:float|dC:float)]|DNA:float|mRNA:float|dC:float|emitter:step[(global_time:any|DNA:any|mRNA:any|dC:any),()])"
  };
}

export const getTestRequest = () => {
  return {
    duration: 11,
    document: getTestDocument()
  }
}