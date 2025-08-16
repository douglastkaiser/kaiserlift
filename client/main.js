import { workerThread } from './worker.js';

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
  try {
    if (createWorker) {
      worker = createWorker();
    } else {
      const blob = new Blob([`(${workerThread.toString()})();`], {
        type: "text/javascript",
      });
      worker = new Worker(URL.createObjectURL(blob), { type: "module" });
    }
  } catch (err) {
    console.error(err);
    result.textContent = "Failed to initialize worker: " + err;
    return;
  }

  const bindUpload = () => {
    const fileInput = doc.getElementById("csvFile");
    const uploadButton = doc.getElementById("uploadButton");
    const progressBar = doc.getElementById("uploadProgress");
    if (!uploadButton || !fileInput) {
      return;
    }
    uploadButton.onclick = async () => {
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
    };
  };

  bindUpload();

  worker.addEventListener("message", (event) => {
    const progressBar = doc.getElementById("uploadProgress");
    if (progressBar) {
      progressBar.value = 100;
      progressBar.style.display = "none";
    }
    if (event.data?.type === "result") {
      result.innerHTML = event.data.html;
      initializeUI(doc);
      bindUpload();
    } else if (event.data?.type === "error") {
      result.textContent = "Failed to process CSV: " + event.data.error;
    }
  });

  worker.addEventListener("error", (event) => {
    console.error("worker error event", event);
    const progressBar = doc.getElementById("uploadProgress");
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
    const msg = details.join(" | ") || "unknown error";
    result.textContent = "Worker error: " + msg;
  });
}

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
