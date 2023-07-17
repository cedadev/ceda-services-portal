// Hide all the changelist-filter lists, so we don't get a jump when changing
// to a select
document.write('<style>#changelist-filter ul { display: none; }</style>');

if( 'django' in window ) {
    (function($) {
        // Once a list has this many items, convert it to a select
        var THRESHOLD = 10;
        var counter = 0;

        $(function() {
            // Find all the filter lists that more than a certain number of items and
            // change them into selects
            $('#changelist-filter ul').each(function() {
                var $list = $(this), $children = $list.children();
                if( $children.length <= THRESHOLD ) {
                    // For lists that are not being replaced, just show them
                    $list.show();
                    return;
                }
                // Build the select
                var $select = $(document.createElement('select'));
                $children.each(function() {
                    var $li = $(this);
                    // Generate a unique id for the original list item
                    var uniqueId = "select-filters-id-" + (counter++);
                    $li.attr('id', uniqueId);
                    // Create the option, using the same text as the list item
                    var $option = $(document.createElement('option'));
                    $option.text($li.text());
                    if( $li.hasClass('selected') ) $option.attr('selected', 'selected');
                    // Store the id of the related list item with the option
                    $option.data('select-filters-id', uniqueId);
                    $select.append($option);
                });
                // When the select is changed, click the corresponding link
                $select.change(function() {
                    var id = '#' + $select.find(":selected").data('select-filters-id');
                    $(id).find('a')[0].click();
                });
                $select.insertBefore($list);
                $list.hide();
            });

            // Find all the selects on the page that are not part of a hidden
            // empty-form and "select2" them
            $('select').not('[multiple]').not('.empty-form select').select2({
                 minimumResultsForSearch : 20,
            });
            $('select[multiple].use-select2').select2();
            // Add a mutation observer that looks for new selects that are
            // added to the page and "select2"s them
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    var newNodes = mutation.addedNodes;
                    if( newNodes !== null ) {
                        $(newNodes)
                            .find('select')
                            .not('[multiple]')
                            .select2({ minimumResultsForSearch : 20 });
                    }
                });
            });
            observer.observe(
                $("body")[0],
                { childList: true, subtree: true, characterData: false }
            );
        });
    })(django.jQuery);
}
