"""
lapq.client — QPU-1 API client.

Get your API key at: https://qpu-1.lovable.app/api-access
"""

from __future__ import annotations

import json
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Literal, Optional, Union

import requests

from lapq.circuit import Circuit
from lapq.models import (
    BatchResult,
    JobResult,
    QuotaInfo,
    TranspileResult,
    ValidateResult,
)

_API_URL      = "https://duqomajwpwjatoroysij.supabase.co/functions/v1/qpu-api"
_GRADIO_URL   = "https://lap-quantum-qpu-1-mcp.hf.space/gradio_api/call/execute"
Format = Literal["qreg", "qiskit", "openqasm"]

_API_KEY_URL = "https://qpu-1.lovable.app/api-access"


class QPU1:
    """
    Python client for the QPU-1 quantum processor by LAP Technologies.

    Parameters
    ----------
    api_key:
        Your QPU-1 API key.  Obtain one at https://qpu-1.lovable.app/api-access
    timeout:
        HTTP timeout in seconds (default 120 s).
    base_url:
        Override the API endpoint (useful for local testing/mocking).

    Quick start
    -----------
    ::

        from lapq import QPU1
        qpu = QPU1("your_api_key_here")

        # Bell state with the fluent circuit builder
        result = qpu.circuit(2).h(0).cnot(0, 1).run()
        print(result.bits)   # "00" or "11"

        # Or use a ready-made algorithm
        from lapq.algorithms import bell_state, grover
        result = bell_state(qpu).run()
    """

    _API_KEY_URL: str = _API_KEY_URL

    def __init__(
        self,
        api_key: str,
        timeout: int = 120,
        base_url: str = _API_URL,
    ) -> None:
        if not api_key or api_key.strip() == "":
            raise ValueError(
                "An API key is required. "
                f"Get yours at {_API_KEY_URL}"
            )
        self._api_key = api_key
        self._timeout = timeout
        self._base_url = base_url
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        })

    # ──────────────────────────────────────────────────────────────────────
    # Low-level helper
    # ──────────────────────────────────────────────────────────────────────

    def _post(self, payload: dict) -> dict:
        resp = self._session.post(
            self._base_url, json=payload, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()

    # ──────────────────────────────────────────────────────────────────────
    # Circuit builder factory
    # ──────────────────────────────────────────────────────────────────────

    def circuit(self, n_qubits: int) -> Circuit:
        """
        Create a new :class:`~lapq.Circuit` for *n_qubits* qubits.

        Example::

            result = qpu.circuit(2).h(0).cnot(0, 1).run()
            print(result.bits)   # "00" or "11"
        """
        return Circuit(n_qubits, self)

    # ──────────────────────────────────────────────────────────────────────
    # Execution
    # ──────────────────────────────────────────────────────────────────────

    def run_qreg(
        self,
        code: str,
        execution_mode: Literal["instant", "overnight"] = "instant",
        max_duration_seconds: Optional[int] = None,
    ) -> JobResult:
        """
        Execute raw Qreg code on QPU-1.

        Parameters
        ----------
        code:
            Qreg source code string.
        execution_mode:
            ``"instant"`` (default) or ``"overnight"`` for long jobs.
        max_duration_seconds:
            Cap execution time (max 300 s).
        """
        return self._execute(
            code=textwrap.dedent(code),
            fmt="qreg",
            execution_mode=execution_mode,
            max_duration_seconds=max_duration_seconds,
        )

    def run_qiskit(
        self,
        code: str,
        execution_mode: Literal["instant", "overnight"] = "instant",
        max_duration_seconds: Optional[int] = None,
    ) -> JobResult:
        """
        Execute Qiskit code on QPU-1 (auto-transpiled server-side).

        The circuit must call ``qc.measure_all()`` or equivalent.

        Example::

            result = qpu.run_qiskit('''
                from qiskit import QuantumCircuit
                qc = QuantumCircuit(2)
                qc.h(0); qc.cx(0, 1); qc.measure_all()
            ''')
            print(result.bits)
        """
        return self._execute(
            code=textwrap.dedent(code),
            fmt="qiskit",
            execution_mode=execution_mode,
            max_duration_seconds=max_duration_seconds,
        )

    def run_openqasm(
        self,
        code: str,
        execution_mode: Literal["instant", "overnight"] = "instant",
        max_duration_seconds: Optional[int] = None,
    ) -> JobResult:
        """
        Execute OpenQASM 2.0 code on QPU-1 (auto-transpiled server-side).

        Example::

            result = qpu.run_openqasm('''
                OPENQASM 2.0;
                include "qelib1.inc";
                qreg q[2]; creg c[2];
                h q[0]; cx q[0],q[1];
                measure q -> c;
            ''')
            print(result.bits)
        """
        return self._execute(
            code=textwrap.dedent(code),
            fmt="openqasm",
            execution_mode=execution_mode,
            max_duration_seconds=max_duration_seconds,
        )

    def run_fast(self, code: str, max_duration_seconds: Optional[int] = None) -> JobResult:
        """
        Shorthand: execute raw Qreg code via the fast Gradio channel.

        The fast channel posts directly to the Gradio ``/execute`` concurrent
        SSE endpoint, bypassing the Supabase API layer for lowest latency.

        Example::

            result = qpu.run_fast("q = Qreg(2)\\nq.H(0)\\nq.CNOT(0,1)\\nprint(q.measure())")
            print(result.bits)   # "00" or "11"
        """
        return self._execute(
            code=textwrap.dedent(code),
            fmt="qreg",
            execution_mode="instant",
            max_duration_seconds=max_duration_seconds,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Fast channel — direct Gradio /execute endpoint
    # ──────────────────────────────────────────────────────────────────────

    def _gradio_execute(self, code: str, timeout) -> JobResult:
        """
        Submit *code* to the Gradio ``/execute`` concurrent SSE endpoint and
        stream the result back.

        This is the same flow as::

            curl -X POST https://lap-quantum-qpu-1-mcp.hf.space/gradio_api/call/execute \
                 -d '{"data": ["..code.."]}' | read EVENT_ID
            curl -N .../execute/$EVENT_ID

        Returns a :class:`~lapq.models.JobResult` with the streamed output.

        The SSE GET uses an **infinite read timeout** because long-running
        QPU jobs (e.g. 256-bit secp256k1) can go minutes between SSE events.
        A finite read timeout kills the socket mid-execution.
        """
        # Connect timeout: 60s is generous; read timeout for POST: finite is OK
        # because the POST just uploads code and returns an event_id.
        connect_timeout = 60
        post_read_timeout = timeout if timeout else 120

        # Step 1: submit and obtain event_id
        resp = self._session.post(
            _GRADIO_URL,
            json={"data": [code]},
            timeout=(connect_timeout, post_read_timeout),
        )
        resp.raise_for_status()
        payload   = resp.json()
        event_id  = payload.get("event_id")
        if not event_id:
            raise ValueError(f"Gradio /execute returned no event_id: {payload}")

        # Step 2: stream SSE result
        # READ TIMEOUT MUST BE NONE — the QPU can run for hours between SSE
        # data events.  A finite read timeout here is the root cause of
        # "random ReadTimeoutError even after the backend is finished".
        result_url = f"{_GRADIO_URL}/{event_id}"
        r = self._session.get(
            result_url,
            timeout=(connect_timeout, None),   # connect=60s, read=forever
            stream=True,
        )
        r.raise_for_status()

        output_text = ""
        for raw_line in r.iter_lines():
            if not raw_line:
                continue
            line_str = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line_str.startswith("data:"):
                try:
                    raw_data = line_str[5:].strip()
                    chunk = json.loads(raw_data)
                    if isinstance(chunk, list) and chunk:
                        val = str(chunk[0])
                        if "/execute" not in val: # Filter out status URLs if any
                            output_text += val
                except Exception:
                    pass

        return JobResult(
            success=True,
            job_id=event_id,
            status="completed",
            output=output_text.strip(),
            raw={"gradio_event": event_id, "channel": "fast"},
        )

    def batch_fast(
        self,
        circuits: List[Union[str, "Circuit"]],
        max_workers: int = 8,
        max_duration_seconds: Optional[int] = None,
    ) -> "BatchResult":
        """
        Execute multiple circuits **concurrently** via the fast Gradio channel.

        Uses :mod:`concurrent.futures.ThreadPoolExecutor` to fire all requests
        in parallel — ideal for parametric sweeps and ensemble measurements.

        Parameters
        ----------
        circuits:
            List of Qreg code strings or :class:`~lapq.Circuit` objects.
        max_workers:
            Maximum concurrent HTTP threads (default 8).
        max_duration_seconds:
            Per-request timeout.

        Returns
        -------
        BatchResult

        Example
        -------
        ::

            results = qpu.batch_fast([
                qpu.circuit(2).h(0).cnot(0,1),
                qpu.circuit(3).ghz(),
            ])
            for r in results:
                print(r.bits)
        """
        timeout = max_duration_seconds  # None = infinite (no read timeout cap)
        codes: List[str] = []
        for c in circuits:
            if isinstance(c, str):
                codes.append(c)
            else:
                codes.append(c.to_qreg(auto_measure=True))

        results: List[JobResult] = [None] * len(codes)  # type: ignore[list-item]

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_idx = {
                pool.submit(self._gradio_execute, code, timeout): idx
                for idx, code in enumerate(codes)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    results[idx] = JobResult(
                        success=False,
                        job_id=None,
                        status="failed",
                        output=str(exc),
                        raw={"error": str(exc)},
                    )

        return BatchResult(
            success=all(r.success for r in results),
            results=results,
            raw={"channel": "fast", "count": len(results)},
        )

    def _execute(
        self,
        code: str,
        fmt: Format = "qreg",
        execution_mode: str = "instant",
        max_duration_seconds: Optional[int] = None,
    ) -> JobResult:
        # Transpile non-Qreg formats first (always via Supabase)
        if fmt != "qreg":
            t = self.transpile(code, from_format=fmt)
            if not t.success:
                return JobResult(False, None, "failed", f"Transpilation failed:\n{t.raw}", t.raw)
            code = t.qreg_code

        # max_duration_seconds=None means "no cap" — DO NOT fall back to
        # self._timeout, which would re-introduce the read timeout bug.
        timeout = max_duration_seconds  # None = infinite in _gradio_execute

        # ── Fast channel (Gradio SSE) is now DEFAULT for all executions ──
        try:
            return self._gradio_execute(code, timeout)
        except Exception as e:
            return JobResult(
                success=False,
                job_id=None,
                status="failed",
                output=str(e),
                raw={"error": str(e), "channel": "fast"},
            )

    # ──────────────────────────────────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────────────────────────────────

    def batch(self, circuits: List[Union[str, dict, Circuit]]) -> BatchResult:
        """
        Execute up to 20 circuits in a single request.

        Each element may be a raw Qreg **string**, a **dict** with ``"code"``
        and optional ``"format"`` keys, or a :class:`~lapq.Circuit` object.

        Example::

            results = qpu.batch([
                {"code": bell_qiskit, "format": "qiskit"},
                {"code": ghz_qiskit,  "format": "qiskit"},
            ])
            for r in results:
                print(r.bits)
        """
        if len(circuits) > 20:
            raise ValueError("batch() accepts at most 20 circuits per request.")
        normalized = []
        for c in circuits:
            if isinstance(c, str):
                normalized.append({"code": c, "format": "qreg"})
            elif isinstance(c, dict):
                normalized.append(c)
            elif isinstance(c, Circuit):
                normalized.append({"code": c.to_qreg(auto_measure=True), "format": "qreg"})
            else:
                raise TypeError(f"Unsupported circuit type: {type(c)}")
        data = self._post({"action": "batch", "circuits": normalized})
        results = [
            JobResult(
                success=r.get("success", data.get("success", False)),
                job_id=r.get("job_id"),
                status=r.get("status", "unknown"),
                output=r.get("output", ""),
                raw=r,
            )
            for r in data.get("results", [])
        ]
        return BatchResult(success=data.get("success", False), results=results, raw=data)

    # ──────────────────────────────────────────────────────────────────────
    # Transpile / validate
    # ──────────────────────────────────────────────────────────────────────

    def transpile(self, code: str, from_format: Optional[str] = None) -> TranspileResult:
        """
        Convert Qiskit or OpenQASM code to Qreg without executing.

        Parameters
        ----------
        code:
            Source code to transpile.
        from_format:
            ``"qiskit"``, ``"openqasm"``, or ``None`` for auto-detect.
        """
        payload: dict = {"action": "transpile", "code": textwrap.dedent(code)}
        if from_format:
            payload["from_format"] = from_format
        data = self._post(payload)
        return TranspileResult(
            success=data.get("success", False),
            qreg_code=data.get("qreg_code", ""),
            original_format=data.get("original_format", ""),
            raw=data,
        )

    def validate(self, code: str, fmt: Format = "qreg") -> ValidateResult:
        """
        Validate code structure without executing it.

        Example::

            v = qpu.validate("q = Qreg(2)\\nq.H(0)\\nprint(q.measure())")
            if not v:
                print(v.issues)
        """
        data = self._post({
            "action": "validate",
            "code": textwrap.dedent(code),
            "format": fmt,
        })
        return ValidateResult(
            success=data.get("success", False),
            valid=data.get("valid", False),
            issues=data.get("issues", []),
            stats=data.get("stats", {}),
            raw=data,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Job management
    # ──────────────────────────────────────────────────────────────────────

    def job_status(self, job_id: str) -> JobResult:
        """Fetch the current status and output of a job by its UUID."""
        data = self._post({"action": "status", "job_id": job_id})
        return JobResult(
            success=data.get("success", False),
            job_id=job_id,
            status=data.get("status", "unknown"),
            output=data.get("output", ""),
            raw=data,
        )

    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> JobResult:
        """
        Poll a job until it reaches a terminal state.

        Parameters
        ----------
        job_id:
            UUID of the job to poll.
        poll_interval:
            Seconds between polls (default 2 s).
        timeout:
            Maximum total wait time in seconds (default 300 s).

        Raises
        ------
        TimeoutError
            If the job has not completed within *timeout* seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            result = self.job_status(job_id)
            if result.status in ("completed", "failed"):
                return result
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Job {job_id!r} did not complete within {timeout}s "
                    f"(last status: {result.status!r})"
                )
            time.sleep(poll_interval)

    def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[Literal["queued", "running", "completed", "failed"]] = None,
    ) -> List[dict]:
        """
        List recent jobs.

        Parameters
        ----------
        limit:
            Max results (default 20, max 100).
        offset:
            Pagination offset.
        status:
            Optional filter: ``"queued"``, ``"running"``, ``"completed"``,
            or ``"failed"``.
        """
        payload: dict = {"action": "list_jobs", "limit": limit, "offset": offset}
        if status:
            payload["status"] = status
        data = self._post(payload)
        return data.get("jobs", [])

    # ──────────────────────────────────────────────────────────────────────
    # Info / utility
    # ──────────────────────────────────────────────────────────────────────

    def quota(self) -> QuotaInfo:
        """Return remaining daily quota and account tier."""
        data = self._post({"action": "quota"})
        q = data.get("quota", {})
        return QuotaInfo(
            jobs_used_today=q.get("jobs_used_today", 0),
            max_jobs_per_day=q.get("max_jobs_per_day", 0),
            max_qubits_per_job=q.get("max_qubits_per_job", 0),
            tier=q.get("tier", "unknown"),
            remaining=q.get("remaining", 0),
        )

    def health(self) -> dict:
        """Return raw health status of the API and QPU."""
        return self._post({"action": "health"})

    def gates(self) -> dict:
        """Return all supported quantum gates grouped by type."""
        data = self._post({"action": "gates"})
        return data.get("gates", {})

    def examples(self) -> dict:
        """Return example quantum circuits from the API."""
        return self._post({"action": "examples"})

    # ──────────────────────────────────────────────────────────────────────
    # Dunder
    # ──────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        masked = self._api_key[:8] + "..." if len(self._api_key) > 8 else "***"
        return f"QPU1(api_key={masked!r}, base_url={self._base_url!r})"
