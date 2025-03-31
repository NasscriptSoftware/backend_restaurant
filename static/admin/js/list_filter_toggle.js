(function($) {
    $(document).ready(function() {
        $('.field-active_status').each(function() {
            var $cell = $(this);
            var $row = $cell.closest('tr');
            var itemId = $row.find('input[name="form-__prefix__-id"]').val();
            
            $cell.html('<button class="toggle-active" data-id="' + itemId + '">' + $cell.text() + '</button>');
        });

        $(document).on('click', '.toggle-active', function(e) {
            e.preventDefault();
            var $button = $(this);
            var itemId = $button.data('id');
            
            $.post('/admin/restaurant_app/sidebaritem/' + itemId + '/toggle-active/', function(data) {
                if (data.success) {
                    $button.text(data.new_status);
                    $button.css('color', data.new_status === 'Active' ? 'green' : 'red');
                }
            });
        });
    });
})(django.jQuery);