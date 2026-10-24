when: the day the tracker's ship_release turns RELEASED (pre-ship payment in, agreement signed, certificate checked, every office has answered)
to: {brand_contact_name} <{brand_contact_email}>
subject: {revised_subject}Your ship date for the {drop_date_long} drop
---
Hi {brand_contact_first},

{revised_line}Payment received, thank you. Your product can ship.

{ship_lines}
- Units: {units_allocated} for {offices} offices, plus {reserve} reserve: {units_to_ship} in all, freight prepaid.
- Every unit sealed, with at least {min_shelf_life_days} days of shelf life left on {drop_date_long} (best-by {best_by_min} or later).
- Please reply with the tracking number and the number of cartons.

Units by office:
{units_table}

The card text we will print is below. Tell me by {card_reply_by_long} if anything is wrong; we print on {kit_print_long}.

{card_text}

{founder_name} · {founder_phone}
---
After sending: on the campaigns tab, log ship_email_sent_date (today) and ship_email_units ({units_to_ship}). If the route changes before the product arrives, the checks ask for a revised email.
