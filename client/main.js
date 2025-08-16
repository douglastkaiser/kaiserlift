export function initializeUI(root = document) {
  if (typeof $ === "undefined") {
    return;
  }
  const tableEl = root.querySelector("#exerciseTable");
  const dropdownEl = root.querySelector("#exerciseDropdown");
  if (!tableEl || !dropdownEl) {
    return;
  }

  const table = $(tableEl).DataTable({ responsive: true });
  $(dropdownEl)
    .select2({ placeholder: "Filter by Exercise", allowClear: true })
    .on("change", function () {
      const val = $.fn.dataTable.util.escapeRegex($(this).val());
      table.column(0).search(val ? "^" + val + "$" : "", true, false).draw();
      $(".exercise-figure").hide();
      const figId = $(this).find("option:selected").data("fig");
      if (figId) {
        $("#fig-" + figId).show();
      }
    });
}

export async function init(createWorker, doc = document) {
  const result = doc.getElementById("result");

  // Ensure the initial UI is usable even if the worker fails to load.
  initializeUI(doc);

  let worker;
  let workerUrl;
  try {
    if (createWorker) {
      worker = createWorker();
    } else {
      workerUrl = new URL("./worker.js", import.meta.url);
      try {
        const response = await fetch(workerUrl, { method: "HEAD" });
        const ct = response.headers.get("content-type");
        console.log(
          `worker.js HEAD status ${response.status}, content-type ${ct}`,
        );
        if (!response.ok || !ct?.includes("javascript")) {
          console.warn(
            `Unexpected worker.js response: status ${response.status}, content-type ${ct}`,
          );
        }
      } catch (err) {
        console.error("Failed to fetch worker.js", err);
      }
      worker = new Worker(workerUrl, { type: "module" });
    }
  } catch (err) {
    console.error(err);
    result.textContent = "Failed to initialize worker: " + err;
    return;
  }

  const fileInput = doc.getElementById("csvFile");
  const uploadButton = doc.getElementById("uploadButton");
  const progressBar = doc.getElementById("uploadProgress");

  worker.addEventListener("message", (event) => {
    if (progressBar) {
      progressBar.value = 100;
      progressBar.style.display = "none";
    }
    if (event.data?.type === "result") {
      result.innerHTML = event.data.html;
      initializeUI(result);
    } else if (event.data?.type === "error") {
      result.textContent = "Failed to process CSV: " + event.data.error;
    }
  });

  worker.addEventListener("error", (event) => {
    console.error("worker error event", event);
    if (progressBar) progressBar.style.display = "none";
    const details = [];
    if (event.message) details.push(event.message);
    if (event.filename) details.push(event.filename);
    if (event.lineno) details.push(`line ${event.lineno}`);
    if (event.colno) details.push(`col ${event.colno}`);
    if (event.error?.message) {
      details.push(event.error.message);
    } else if (event.error) {
      details.push(event.error.toString());
    }
    if (workerUrl) details.push(`script: ${workerUrl}`);
    const msg = details.join(" | ") || "unknown error";
    result.textContent = "Worker error: " + msg;
  });

  uploadButton.addEventListener("click", async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      result.textContent = "Please select a CSV file.";
      return;
    }

    if (progressBar) {
      progressBar.style.display = "block";
      progressBar.value = 0;
    }

    try {
      const text = await file.text();
      if (progressBar) progressBar.value = 50;
      worker.postMessage({ csv: text });
    } catch (err) {
      console.error(err);
      if (progressBar) progressBar.style.display = "none";
      result.textContent = "Failed to read file: " + err;
    }
  });
}

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
