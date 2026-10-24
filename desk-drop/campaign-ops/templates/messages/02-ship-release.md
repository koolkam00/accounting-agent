when: the day the tracker's ship_release turns RELEASED (payment in, agreement signed, certificate checked, offices approved)
to: {brand_contact_name} <{brand_contact_email}>
subject: Your ship date for the {drop_date_long} drop
---
Hi {brand_contact_first},

Payment received, thank you. Your product can ship.

- Ship by: {ship_by_requested_long} (latest {cancel_by_long}). It must arrive by {receive_by_long}.
- Ship to: {ship_to}
- Units: {units_allocated} for {offices} offices, plus {reserve} reserve: {units_to_ship} in all, freight prepaid.
- Every unit sealed, with at least {min_shelf_life_days} days of shelf life left on {drop_date_long} (best-by {best_by_min} or later).
- Please reply with the tracking number and the number of cartons.
{direct_ship_block}
Units by office:
{units_table}

The card text we will print is below. Tell me by {card_reply_by_long} if anything is wrong; we print on {kit_print_long}.

{card_text}

{founder_name} · {founder_phone}
