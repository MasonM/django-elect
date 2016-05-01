;(function ($) {
    $(document).ready(function() {
        /* Hides the "Vote preferentials" and "Vote pluralities" forms unless
         * an election is selected, since we need the election for autocomplete
         * to work on the candidate drop-downs. */
        var inline_groups = $('#pluralities-group, #preferentials-group');
        $('#id_election').on('change', function() {
            inline_groups.toggle($(this).val() !== '');
        }).trigger('change');
    });
})(django.jQuery);
