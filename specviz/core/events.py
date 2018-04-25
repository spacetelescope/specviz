from .dispatch import Dispatch


dispatch = Dispatch()

dispatch.register_event("on_activated_window", args=["window"])

dispatch.register_event("on_added_data", args=["data"])
dispatch.register_event("on_added_window", args=["layer", "window"])
dispatch.register_event("on_added_plot", args=["plot", "window"])
dispatch.register_event("on_added_layer", args=["layer"])
dispatch.register_event("on_added_to_window", args=["layer", "window", "style"])

dispatch.register_event("on_show_linelists_window")
dispatch.register_event("on_dismiss_linelists_window", args=["close"])
dispatch.register_event("on_request_linelists")
dispatch.register_event("on_plot_linelists", args=["table_views", "panes", "units", "caller"])
dispatch.register_event("on_erase_linelabels", args=["caller"])
dispatch.register_event("mouse_enterexit", args=["event_type"])

dispatch.register_event("on_removed_data", args=["data"])
dispatch.register_event("on_removed_plot", args=["layer", "window"])
dispatch.register_event("on_removed_layer", args=["layer", "window"])
dispatch.register_event("on_removed_model", args=["model", "layer"])
dispatch.register_event("on_removed_from_window", args=["layer", "window"])

dispatch.register_event("on_updated_layer", args=["layer"])
dispatch.register_event("on_updated_model", args=["model"])
dispatch.register_event("on_updated_plot", args=["plot", "layer"])
dispatch.register_event("on_updated_rois", args=["rois"])
dispatch.register_event("on_updated_stats", args=["stats", "layer"])

dispatch.register_event("on_selected_plot", args=["layer", "checked_state"])
dispatch.register_event("on_selected_window", args=["window"])
dispatch.register_event("on_selected_layer", args=["layer_item"])
dispatch.register_event("on_selected_model", args=["model_item"])

dispatch.register_event("on_clicked_layer", args=["layer_item"])
dispatch.register_event("on_changed_layer", args=["layer_item"])
dispatch.register_event("on_changed_model", args=["model_item"])
dispatch.register_event("on_copy_model")
dispatch.register_event("on_paste_model", args=["data", "layer"])

dispatch.register_event("on_add_data", args=["data"])
dispatch.register_event("on_add_model", args=["layer", "model"])
dispatch.register_event("on_add_window", args=["data", "window", "layer"])
dispatch.register_event("on_add_layer", args=["window", "layer", "from_roi", "style"])
dispatch.register_event("on_add_roi", args=[])
dispatch.register_event("on_add_to_window", args=["data", "layer", "window", "style", "vertical_line"])

dispatch.register_event("on_update_model", args=["layer"])

dispatch.register_event("on_remove_data", args=["data"])
dispatch.register_event("on_remove_layer", args=["layer"])
dispatch.register_event("on_remove_model", args=["model"])
dispatch.register_event("on_remove_all_data")

dispatch.register_event("on_file_open", args=["file_name"])
dispatch.register_event("on_file_read", args=["file_name", "file_filter", "auto_open"])

dispatch.register_event("on_status_message", args=["message", "timeout"])
dispatch.register_event("changed_dispersion_position", args=["pos"])
dispatch.register_event("change_dispersion_position", args=["pos"])
dispatch.register_event("finished_position_change")
dispatch.register_event("changed_roi_mask", args=["mask"])
dispatch.register_event("changed_units", args=["x", "y"])
dispatch.register_event("performed_operation", args=["operation"])
dispatch.register_event("apply_function", args=["func"])
dispatch.register_event("apply_operations", args=["stack"])
dispatch.register_event("added_roi", args=["roi"])
dispatch.register_event("removed_roi", args=["roi"])
dispatch.register_event("change_redshift", args=["redshift"])
dispatch.register_event("toggle_layer_visibility", args=["layer", "state"])
dispatch.register_event("load_model_from_dict", args=["model_dict"])
dispatch.register_event("replace_data", args=['old_data', 'new_data'])
dispatch.register_event("replace_layer", args=['old_layer', 'new_layer', 'style'])