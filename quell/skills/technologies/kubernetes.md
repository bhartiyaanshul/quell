---
name: kubernetes
category: technologies
description: Kubernetes pod lifecycle, scheduling, and cluster-level incident patterns
applicable_when:
  - tech_stack_includes: "kubernetes"
  - tech_stack_includes: "k8s"
  - error_contains: "CrashLoopBackOff"
  - error_contains: "ImagePullBackOff"
  - error_contains: "ErrImagePull"
  - error_contains: "OOMKilled"
  - error_contains: "FailedScheduling"
  - error_contains: "CreateContainerError"
  - error_contains: "Pending"
  - error_contains: "Evicted"
severity_hint: high
---

# Kubernetes incident cheatsheet

## Where to look first
- **`kubectl describe pod <pod>`** — the Events section at the bottom
  is almost always where the real error lives. Warnings are the
  signal; Normal is noise.
- **Container-level logs.** `kubectl logs <pod> -c <container>
  --previous` for the last crashed instance. Without `--previous`
  you get the current (often unhelpful) instance.
- **Resource state.** `kubectl top pods` + `kubectl top nodes`.
  OOM-killed pods won't show live, but `kubectl describe` will show
  the "Last State: Terminated, Reason: OOMKilled".

## Common failure shapes
- **`CrashLoopBackOff`.** Container starts, exits non-zero, kubelet
  backs off exponentially. Causes: app crashed on boot (missing env
  var, can't reach DB), `command:` / `args:` wrong, readiness probe
  failing against a process that hasn't finished initial load.
- **`ImagePullBackOff` / `ErrImagePull`.** Registry auth missing
  (`imagePullSecrets`), tag doesn't exist, or private registry not
  reachable from the node network.
- **`OOMKilled`.** Container's `resources.limits.memory` is lower
  than its real peak usage. Observe peak with `kubectl top` or
  a profiler. Bump the limit *and* find the leak (see `memory-leak`
  skill).
- **`Pending` / `FailedScheduling`.** No node satisfies the pod's
  resource requests, node selector, or taints/tolerations. `kubectl
  describe pod` shows the last scheduling attempt's reasons.
- **`Evicted`.** Node ran out of a resource (memory, disk, inodes)
  and chose this pod. Check `kubectl describe node <node>` Events
  for `DiskPressure` / `MemoryPressure`.
- **CrashLoopBackOff with "liveness probe failed"** — the probe is
  firing before the app is ready. Add a `startupProbe` or extend
  `initialDelaySeconds`.

## Useful commands
- `kubectl get events --sort-by=.lastTimestamp -A | tail -30` — recent
  cluster-wide activity.
- `kubectl exec -it <pod> -- sh` — interactive shell when the
  container stays up long enough.
- `kubectl debug <pod> -it --image=alpine --target=<container>` —
  attach a debugging sidecar without modifying the pod spec.
- `kubectl get pod <pod> -o yaml` — see exactly what was submitted,
  including any admission-controller mutations.
