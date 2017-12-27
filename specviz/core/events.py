from .dispatch import Dispatch


dispatch = Dispatch()

dispatch.register_event("on_activated_window", args=["window"])

dispatch.register_event("on_added_data", args=["data"])
dispatch.register_event("on_added_window", args=["layer", "window"])
dispatch.register_event("on_added_plot", args=["plot", "window"])
dispatch.register_event("on_added_layer", args=["layer"])
dispatch.register_event("on_added_to_window", args=["layer", "window", "style"])

dispatch.register_event("on_show_linelists_window")
dispatch.register_event("on_dismiss_linelists_window")
dispatch.register_event("on_request_linelists")
dispatch.register_event("on_plot_linelists", args=["table_views", "tabbed_panes", "units"])
dispatch.register_event("on_erase_linelabels")

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
dispatch.register_event("on_add_to_window", args=["data", "window", "style"])

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
dispatch.register_event("changed_roi_mask", args=["mask"])