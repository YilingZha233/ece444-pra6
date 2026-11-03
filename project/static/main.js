// Use an explicit button so selecting or reading a post does not delete it.
document.querySelectorAll(".delete-entry").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    const error = document.getElementById("delete-error");
    try {
      const response = await fetch(`/delete/${button.dataset.postId}`);
      const result = await response.json();
      if (!response.ok || result.status !== 1) {
        throw new Error(result.message || "Unable to delete this entry.");
      }
      window.location.reload();
    } catch (problem) {
      error.textContent = problem.message;
      error.hidden = false;
      button.disabled = false;
    }
  });
});
