# Production-Grade PINN-Ops: Low Latency SciML Inference Engine with GitOps Continuous Validation

![PINN Inference Interface Demo](frontend/Demo.gif)

This repository contains a production-ready, high-throughput inference service designed to serve a Physics-Informed Neural Network (PINN) spatiotemporal surrogate model. The architecture bridges deep learning with systems engineering by optimizing a raw PyTorch model into a static computation graph, deploying it within a containerized multi-worker ASGI environment, and enforcing a strict GitOps continuous validation gate.

---

## Architecture Blueprint

### 1. Compiled SciML Compute Core
Surrogate physics models require microsecond execution speeds to be viable alternatives to traditional numerical solvers. During the application startup lifespan phase, the dynamic PyTorch model is trace-compiled using TorchScript JIT compilation against an empty coordinate tensor. This process evaluates out the Python interpreter completely, flattening the multi-layer perceptron into an optimized, serialized C++ static execution graph. This compilation bypasses the Global Interpreter Lock (GIL) and optimizes matrix evaluation directly on the host processor.

### 2. High-Concurrency Asynchronous Serving Layer
The runtime engine leverages FastAPI built on top of an Asynchronous Server Gateway Interface (ASGI) topology. To maximize CPU utilization and scale horizontally across host cores, the deployment manages four parallel Uvicorn worker processes. Incoming JSON payloads representing spatiotemporal coordinates ($x, y, t$) are validation-checked instantly via strict Pydantic models before being dispatched across available worker processes, eliminating network serialization bottlenecks and preventing query queuing.

### 3. Hardened Enterprise Container Design
The service is fully containerized using a lightweight Alpine Linux base runtime image. To defend against privilege escalation exploits within the host kernel, the runtime space drops root privileges entirely. The container establishes an isolated system group and standard non-privileged execution profile (`appuser`), maintaining strict ownership boundaries over the serialized model weights and static web layouts.

### 4. GitOps Automated Continuous Validation
The quality assurance layer treats system performance as a blocking unit test. Pushing code to target branches kicks off a headless GitHub Actions cloud runner. The pipeline orchestrates a clean build environment, launches the application container, introduces an explicit temporal delay to absorb worker graph compilation warmups, and triggers a multi-threaded parallel stress test. Rather than evaluating generic math averages, the regression gate sorts response distribution blocks to track tail anomalies. If throughput slips or tail metrics break predefined limits, the pipeline terminates the build.

---

## Deployment Structure

        [ Spatial/Temporal Inputs ] -> (x, y, t)
                    |
                    v
        +-----------------+
        |  Frontend (UI)  | -> Served via FastAPI StaticFiles Mount
        +-----------------+
                    |
                    v (Async JSON Fetch Payload)
        +------------------------------------------------------------+
        | Docker Container Boundary (Non-Root Privileges / appuser)  |
        |                                                            |
        |  [ Port 8000 Inbound Gateway ]                             |
        |            |                                               |
        |            v                                               |
        |   +----------------------------------------------------+   |
        |   | Master Uvicorn Process (Load Balancer)             |   |
        |   +----------------------------------------------------+   |
        |        |             |               |              |      |
        |        v             v               v              v      |
        |   +--------+    +--------+      +--------+     +--------+  |
        |   | Worker |    | Worker |      | Worker |     | Worker |  |
        |   |   #1   |    |   #2   |      |   #3   |     |   #4   |  |
        |   +--------+    +--------+      +--------+     +--------+  |
        |        |             |               |              |      |
        |        +-------------+-------+-------+--------------+      |
        |                              |                             |
        |                              v                             |
        |                 +--------------------------+               |
        |                 | Pydantic Input Validation|               |
        |                 +--------------------------+               |
        |                              |                             |
        |                              v                             |
        |                 +--------------------------+               |
        |                 | JIT TorchScript Engine   |               |
        |                 | (Compiled C++ Surrogacy) |               |
        |                 +--------------------------+               |
        |                              |                             |
        |                              v                             |
        |                     [ Tensor Forward Pass ]                |
        |                              |                             |
        +------------------------------|-----------------------------+
                                        v
                            {"predicted_temperature": float}

## Performance Benchmarks

The following operational metrics were verified under full parallel load simulation across concurrent thread arrays:

| Performance Metric | Evaluation Value | Quality Gate Target | Result Status |
| :--- | :--- | :--- | :--- |
| **Sustained Throughput** | 616.52 req/sec | > 100.0 req/sec | Passed |
| **p95 Tail Latency** | 21.05 ms | < 100.0 ms | Passed |
| **p99 Tail Latency** | 24.49 ms | < 150.0 ms | Passed |
| **Transaction Success Rate** | 100.0% | 100.0% | Passed |

---

## Directory Taxonomy

```text
├── .github/
│   └── workflows/
│       └── ci.yml             # GitOps continuous validation workflow
├── frontend/
│   ├── app.js                 # Network request orchestrator 
│   ├── Demo.gif               # Animated user interface dashboard demonstration
│   ├── index.html             # Document structure layout
│   └── style.css              # Typography and component styling layouts
├── Dockerfile                 # Hardened non-root multi-worker image layout
├── load_server.py             # Parallel stress test verification suite
├── model.pt                   # Serialized neural network weights
├── requirements.txt           # Explicit version-locked python dependencies
└── server.py                  # Compiled FastAPI server orchestration engine
```

## Local Deployment Quickstart

1. Execute Production Image Compilation
Compile the hardened container image using the local directory context:
`docker build -t pinn-inference:latest .`

2. Launch the High-Concurrency Container
Spin up the isolated container service, mapping the application gateway port directly to the host machine:
`docker run -d -p 8000:8000 --name pinn-container pinn-inference:latest`

3. Access Internal Diagnostic Interface
Open a secure browser window and connect directly to the active networking endpoint to evaluate live model inference loops visually:
`http://localhost:8000`

4. Execute the Regression Test Suite Manually
To stress-test your running local infrastructure container and audit system latencies under load, execute the automated verification layer directly:
`python load_server.py`
