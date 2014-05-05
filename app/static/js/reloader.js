/**
 * Created by cruor on 5/5/14.
 */
var auto_refresh = setInterval(function () {
    $('.View').fadeOut('slow', function() {
        $(this).load('/mcoutput', function() {
            $(this).fadeIn('slow');
        });
    });
}, 15000);