/* Namespace for core functionality related to DataTables. */
horizon.datatables = {
  timestamp_query: performance.now(),
  pending_request: undefined,
};

horizon.datatables.add_no_results_row = function (table) {
  /*// Add a "no results" row if there are no results.
  template = horizon.templates.compiled_templates["#empty_row_template"];
  if (!table.find("div.list-group-item:visible").length
      && typeof(template) !== "undefined") {
    table.append(template.render());
  }*/
  table.find("p.empty").show();
};

horizon.datatables.remove_no_results_row = function (table) {
  table.find("p.empty").hide();
};

horizon.datatables.ajax_paginate = function(params) {
  var page_num = params.page_num || 1;
  var table = params.table;

  if (!table.attr('data-pagination-url')) {
    horizon.datatables.remove_no_results_row(table);
    return;
  }
  var table_selector = table.attr('id');
  var id_for_spinner = params.tab_group_id || table_selector;

  horizon.ajax.queue({
    type: 'GET',
    url: table.attr('data-pagination-url'),
    data: {
      page: page_num,
      application_id: table.attr('data-application_id'),
      application_role:table.attr('data-application_role'),
      organization_id: table.attr('data-organization_id'),
      organization_role:table.attr('data-organization_role'),
      user_id: table.attr('data-user_id'),
      name__startswith: table.find('div.table_search.client input').val() || undefined,
    },
    beforeSend: function () {
      $('#spinner_' + id_for_spinner).show();
      horizon.datatables.remove_no_results_row(table);
    },
    complete: function () {
      $('#spinner_' + id_for_spinner).hide();
    },
    error: function(jqXHR, status, errorThrown) {
    },
    success: function (data, textStatus, jqXHR) {
      var list_group = $('#'+table_selector).find('div.list-group');
      list_group.empty();

      // process data
      var items = data['items'];
      if (items.length) {
        horizon.datatables.remove_no_results_row(table);
      } else {
        horizon.datatables.add_no_results_row(table);
      }
      var template = horizon.templates.compiled_templates["#table_row_template"];
      for (var i in items) {
        list_group.append(template.render(items[i]));
      }

      // reinitialize pagination
      horizon.datatables.init_pagination(table, data['pages'], params.register_event);
    }
  });
}
horizon.datatables.init_pagination = function (table, total_pages, register_event) {
  if (total_pages <= 0) {
    // to force pagination clearing, we set page to 1
    total_pages = 1;
  }

  if (register_event === undefined) {
    register_event = true;
  }

  // init bootpag
  var pagination = $('#'+table.attr('id')+'_pagination_container');
  pagination.bootpag({
      total: total_pages,
      first: 'First',
      last:'Last',
      maxVisible: 10,
      wrapClass: 'pagination',
      firstLastUse: true,
      leaps: true
  })
  if (register_event == true) {
    pagination.on("page", function(event, page_num){
      horizon.datatables.ajax_paginate({
        table: table, 
        page_num: page_num, 
        register_event: false
      });
    });
  }
};

horizon.datatables.set_pagination_filter = function(params) {
  var MIN_TIME_BETWEEN_QUERIES = 600; // ms
  var MIN_LETTERS_TO_QUERY = -1;

  var table = params.table;

  table.find('div.table_search.client input').on('input', function() {
    var $input = $(this);
    var filter_data = $input.attr('value');
    if (filter_data.length < MIN_LETTERS_TO_QUERY){
      return;
    }

    var dif =  performance.now() - horizon.datatables.timestamp_query;
    if(dif < MIN_TIME_BETWEEN_QUERIES){
      if (horizon.datatables.pending_request !== undefined) {
        // kill previous request
        window.clearTimeout(horizon.datatables.pending_request);
      }
    }

    //store query time
    horizon.datatables.timestamp_query = performance.now();

    horizon.datatables.pending_request = window.setTimeout(function() {
        horizon.datatables.ajax_paginate({
          table: table, 
          page_num: 1, 
          register_event: false
        });
      }, MIN_TIME_BETWEEN_QUERIES);
  });

};

horizon.datatables.set_table_query_filter = function (parent) {
  horizon.datatables.qs = {};
  $(parent).find('div.panel').each(function (index, elm) {
    var input = $($(elm).find('div.table_search.client input')),
        table_selector;
    if (input.length > 0) {
      // Disable server-side searching if we have client-side searching since
      // (for now) the client-side is actually superior. Server-side filtering
      // remains as a noscript fallback.
      // TODO(gabriel): figure out an overall strategy for making server-side
      // filtering the preferred functional method.
      input.on('keypress', function (evt) {
        if (evt.keyCode === 13) {
          return false;
        }
      });
      input.next('button.btn span.fa-search').on('click keypress', function (evt) {
        return false;
      });

      // Enable the client-side searching.
      table_selector = '#' + $(elm).find('div.list-group').attr('id');

      var qs = input.quicksearch(table_selector + ' div.list-group-item', {
        'delay': 300,
        'loader': 'span.loading',
        'bind': 'keyup click',
        'show': this.show,
        'hide': this.hide,
        onBefore: function () {
          var table = $(table_selector);
          horizon.datatables.remove_no_results_row(table);
        },
        onAfter: function () {
          var template, table, colspan, params;
          table = $(table_selector);
          horizon.datatables.add_no_results_row(table);
        },
        prepareQuery: function (val) {
          return new RegExp(val, "i");
        },
        testQuery: function (query, txt, _row) {
          return query.test($(_row).find('div.filter_field:not(.hidden):not(.actions_column)').text());
        }
      });
    }
  });
};


horizon.addInitFunction(function() {
  $('div.datatable').each(function (idx, el) {
    var tab_group_id;
    var tab_content = $(el).parents('div.tab-content').attr('id');

    if (tab_content) {
      tab_group_id = tab_content.replace('body_', '');
    }

    // load intial elements
    horizon.datatables.ajax_paginate({
      table: $(el), 
      page_num: 1, 
      register_event: true, 
      tab_group_id: tab_group_id
    });

    // set up filter
    horizon.datatables.set_pagination_filter({table: $(el)})
  });

  // Trigger run-once setup scripts for tables.
  //horizon.datatables.set_table_query_filter($('body'));

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);

  // Also apply on tables in tabs views for lazy-loaded data.
  horizon.tabs.addTabLoadFunction(horizon.datatables.ajax_paginate);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_pagination_filter);

});
