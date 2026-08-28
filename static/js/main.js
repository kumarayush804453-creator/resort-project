function goToBookingFromModal(modalId) {
    var modalElement = document.getElementById(modalId);
    var modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) {
        modalInstance.hide();
    }
    setTimeout(function() {
        document.getElementById('book').scrollIntoView({ behavior: 'smooth' });
    }, 300);
}