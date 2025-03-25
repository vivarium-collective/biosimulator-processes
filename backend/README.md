# `biosimulator-processes/backend`: Composition API Server

### _This project uses the following tooling_:
- `air`: hot-reloads Go modules (`gateway` and `server`). Each of these mods has a corresponding `.air.toml` which configures this setup.
- `tilt`: Emulates k8 deployment locally for all microservices and also provides hot reloads. This tooling is configured by the `Tiltfile` at `./backend`

### **_REMINDERS REGARDING GOLANG CONTENT_**:
1. **Be sure to periodically run:** 
	```bash
	gofmt -w <GO FILE PATH>
	```

2. **Public func names are in `PascalCase`, while private func names are in `camelCase`**

3. **Get (filter) funcs usually should return a tuple of [Data, errors (if any)] like:**
	```go
	if val, ok := GetNested(cfg, "geometry", "meta", "created_by"); ok {
		fmt.Println("Found:", val)
	```

4. **The proto module found at `./proto` is configured and setup using the `Makefile` found within the directory. To regenerate `.proto` files, simply run:**
	```bash
	cd proto
	make 
	```

5. **`./gateway` and `./server` Go modules are configured by calling the script found at `./scripts/go_init.sh`, passing the given module name as an argument. `server` for example:**
	```bash
	./scripts/go_init.sh server
	```


### **Configuring microservices for deployment**:
This project uses docker to containerize the microservices. Consider the following setup instructions:

**Building `./gateway` or `./server` (_Go_ microservices):**
```docker
# For example, gateway:
RUN cd /app/gateway && go install
```

**Building `./runner` (_Python_ microservice):**
```docker
WORKDIR /app
COPY ./backend/runner /app
RUN uv sync --frozen --all-extras
```

#### **_Why Go instead of Python?_**:
This app offloads orchestration & stream management to a fast, memory-efficient binary.
You can deploy & monitor the Go services independently from your Python models. More to come...

