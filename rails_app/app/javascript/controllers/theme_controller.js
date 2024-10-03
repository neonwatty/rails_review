import { Controller } from "@hotwired/stimulus";

// Connects to data-controller="theme"
export default class extends Controller {
  static targets = ["checkbox"];

  connect() {
    this.loadCheckboxState();
  }

  saveCheckboxState() {
    document.documentElement.classList.toggle("dark");
    localStorage.setItem("appTheme", this.checkboxTarget.checked);
  }

  loadCheckboxState() {
    const savedState = localStorage.getItem("appTheme");
    this.checkboxTarget.checked = savedState === "true";
    if (this.checkboxTarget.checked) {
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
    }
  }
}
