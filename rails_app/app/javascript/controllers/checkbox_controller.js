import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["checkbox", "output"];

  connect() {
    this.loadCheckboxStates();
    console.log('Checkbox controller connected');
    this.showBoxesChecked(); // Initial display of checked checkboxes
  }

  get checkedCheckboxes() {
    return this.checkboxTargets
      .filter(checkbox => checkbox.checked)
      .map(checkbox => checkbox.value);
  }

  checkStatus(event) {
    const checkbox = event.target;
    const index = checkbox.id.split('-')[1]; // Extract the index from the checkbox ID
    this.saveCheckboxState(index, checkbox.checked);
    this.showBoxesChecked(); // Update the display after checking/unchecking
  }

  saveCheckboxState(index, isChecked) {
    localStorage.setItem(`checkbox-${index}`, isChecked);
  }

  loadCheckboxStates() {
    this.checkboxTargets.forEach((checkbox, index) => {
      const savedState = localStorage.getItem(`checkbox-${index}`);
      checkbox.checked = savedState === 'true';
    });
  }

  showBoxesChecked() {
    this.outputTarget.textContent = this.checkedCheckboxes.length > 0
      ? this.checkedCheckboxes.join(', ')
      : 'No checkboxes selected.';
  }
}
