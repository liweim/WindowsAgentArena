# Windows accessibility task naturalness and web-drift audit

审计日期：2026-10-09。范围：`evaluation_examples_windows/examples` 下 200 个任务。

## 口径

- “可能性”判断的是目标用户在真实 Windows 使用中是否可能遇到同类需求，不代表人群患病率或任务频率。
- 自然性：A = 自然且 task–need fit 强；B = 场景可成立但有明显 benchmark/机械化表达；C = 主要适合作为压力测试、角色很窄或需要重写。
- “运行风险”只看执行时是否依赖公网页面/在线服务；“出处风险”也包括已下载到本地、运行不再依赖公网的原始来源。
- `host.docker.internal`、本地文件、固定 Kiwix Wikipedia、OneStopShop/CMS/forum/CAPTCHA 视为可控环境；其风险主要是镜像/种子维护，不是公网网页漂移。

## 汇总

- 数量：visual 50，hearing 50，motor 50，cognitive 50。
- 自然性：A 141，B 32，C 27。没有发现从能力定义上绝对“不可能”的任务，但 C 类不宜作为日常生态任务来表述。
- 运行时网页风险：高 19，中 11，低 170。12 个高风险内容型任务已改用本地 PDF。
- 总体判断：hearing 与 cognitive 的提醒/清单/字幕任务整体最自然；motor 指令现已用真实输入困难解释辅助功能的用途，明显减轻了“设置 + 无关任务”的拼接感；CAPTCHA 仍应明确标为 stress-test slice。

## 逐任务判断

| 用户组 | 任务 ID | 现实可能性 | 自然性 | 运行风险 | 出处风险 | 简要依据 |
|---|---|---|:---:|:---:|:---:|---|
| cognitive | access-chrome_font_size_large | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | access-chrome_immersive_reader_extension | 很可能/合理场景 | B | 高 | 中-高 | 安装阅读辅助扩展合理，但指定低使用量第三方扩展较人为且有供应链风险 |
| cognitive | access-edge_immersive_reader_setup | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | access-windows_notification_duration | 很可能/合理场景 | C | 低 | 低 | 需求合理，但要求普通用户直接改注册表且解释系统缺控件，表达不自然 |
| cognitive | access-windows_text_size_125 | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | captcha-audio_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| cognitive | captcha-click_sequence_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| cognitive | captcha-click_sequence_4 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| cognitive | captcha-count_chars_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| cognitive | captcha-count_chars_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| cognitive | communication-ftc_gift_card_pressure_email | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | communication-ftc_gift_card_scam_email | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | communication-ftc_spam_text_safety_email | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | communication-library_program_reply | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | communication-volunteer_shift_reply | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-elsa_water_bottle | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-ginger_ale_note | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-kids_sunscreen_reviews | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-lowest_price_white_mouse | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-movie_night_shopping | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | consumption-tomato_egg_stir_fry | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | health-doctor_appointment_preparation | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | health-doctor_visit_preparation_summary | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | health-medication_change_calendar | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | health-morning_care_reminders | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | health-running_hydration_guide_note | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | health-sunscreen_ingredient_age_note | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | information-chrome_reference_bookmarks | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | information-emergency_kit_checklist | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | information-food_calorie_forum_answer | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | information-passport_renewal_checklist | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | information-running_hydration_note | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | information-wikipedia_accessibility_definition | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | management-cfpb_autopay_review_reminder | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | management-medication_timer | 很可能/合理场景 | A | 高 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | management-prescription_refill_reminder | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | management-sunscreen_ingredient_reminder | 很可能/合理场景 | B | 低 | 中-高 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | management-water_payment_spreadsheet | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | management-weekly_planning_reminder | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | mobility-babson_bow_shuttle_plan | 很可能/合理场景 | A | 低 | 高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | mobility-harvard_mather_evening_plan | 很可能/合理场景 | A | 低 | 高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | mobility-nih_after_hours_entry_note | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | mobility-victoria_train_interchange_note | 很可能/合理场景 | A | 低 | 高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | mobility-wmata_a49_morning_plan | 很可能/合理场景 | A | 低 | 高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| cognitive | service-cms_delete_obsolete_pickup_page | 条件性（仅网站/CMS 管理角色） | B | 低 | 低 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | service-cms_import_service_product | 条件性（仅网站/CMS 管理角色） | B | 低 | 低 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | service-cms_product_record | 条件性（仅网站/CMS 管理角色） | B | 低 | 低 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | service-cms_schedule_policy_review | 条件性（仅网站/CMS 管理角色） | B | 低 | 低 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| cognitive | service-cms_simplify_service_hours | 条件性（仅网站/CMS 管理角色） | A | 低 | 低 | 清晰化网页内容直接对应可读性需求，目标和产物自然 |
| cognitive | service-cms_update_voyage_stock | 条件性（仅网站/CMS 管理角色） | B | 低 | 低 | 目标可能真实，但逐字复制/固定字段或职业流程使指令偏机械 |
| hearing | access-chrome_live_caption_language | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_audio_flash_title_bar | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_audio_flash_window | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_caption_text_large | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_live_caption | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_mono_audio_screen_flash | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | access-windows_notification_5_minutes | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | captcha-audio_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| hearing | captcha-audio_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| hearing | captcha-audio_4 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| hearing | communication-community_class_registration | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | communication-dental_reschedule_voicemail | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | communication-equipment_reimbursement_email | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | communication-meeting_action_items | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | communication-passport_photo_checklist_email | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | communication-pharmacy_pickup_voicemail | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-colgate_slimsoft_six_pack | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-dyson_travel_case | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-ginger_ale | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-insta360 | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-order_substitution_audio | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | consumption-sony_alpha | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-allergy_medication | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-anaphylaxis_medicine | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-celiac_disease_treatment | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-child_visit_preparation | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-long_covid_care_note | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | health-sepsis_act_fast | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-apartment_maintenance | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-fake_job_bank_account | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-ftc_2024_fraud_reports | 很可能/合理场景 | A | 高 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-ftc_florida_fraud_data | 很可能/合理场景 | A | 高 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-ftc_washington_q4_fraud | 很可能/合理场景 | A | 高 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-handwashing_steps | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-laundry_tag_investigation | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-maricopa_census_search | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | information-noaa_pillow_lava | 很可能/合理场景 | A | 中 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | management-double_dough_timer | 很可能/合理场景 | A | 高 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | management-dryer_cycle_timer | 很可能/合理场景 | A | 高 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | management-home_delivery_window_audio | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | management-quick_sponge_timer | 很可能/合理场景 | A | 高 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | management-service_appointment_audio | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | mobility-opera_house_street_view | 很可能/合理场景 | A | 高 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | mobility-walking_route_alhambra | 很可能/合理场景 | A | 高 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | mobility-zion_large_group_route | 很可能/合理场景 | A | 高 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | service-cms_update_access_desk_page_audio | 条件性（仅网站/CMS 管理角色） | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | service-cms_update_voyage_stock_audio | 条件性（仅网站/CMS 管理角色） | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | service-council_document_pickup_audio | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | service-irs_ip_pin_alternative_form | 很可能/合理场景 | A | 高 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| hearing | service-ssa_replacement_card_start | 很可能/合理场景 | A | 高 | 中-高 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-enable_clicklock | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-enable_filter_keys | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-enable_mouse_keys | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-enable_on_screen_keyboard | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-enable_sticky_keys | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | access-set_primary_mouse_button_right | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| motor | captcha-click_sequence_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-geometry_click_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-hold_button_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-patch_select_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-robot_checkbox_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-slide_puzzle_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | captcha-slide_puzzle_3 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| motor | communication-filter_keys_volunteer_email | 很可能/合理场景 | A | 低 | 高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | communication-meeting_agenda_draft | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | communication-mouse_keys_equipment_update_email | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | communication-osk_referral_email | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-cheapest_bathroom_accessory | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-cheapest_polisher | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-half_price_body_wash | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-running_shoe_release_comparison | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-shopping_list_cart | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | consumption-wireless_mouse_search_result | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-allied_health_form_download | 很可能/合理场景 | A | 高 | 中-高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-insulin_storage_temperature | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-parkinsons_medication_reminders | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-physiotherapy_appointment_checklist | 很可能/合理场景 | A | 低 | 中-高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-sticky_keys_emergency_contact_card | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | health-wheelchair_charging_timer | 很可能/合理场景 | A | 高 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-bookmark_accessibility_reference | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-psychology_coursework_upload_limit | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-singapore_real_gdp_comparison | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-skill_building_hobbies | 很可能/合理场景 | A | 低 | 中-高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-touchpad_cleaning_instructions | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-ucla_economics_premajor_gpa | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | information-world_cup_winners_hosts | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | management-electricity_bill_payment | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | management-monthly_expenses_total | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | management-next_meeting_calendar | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | management-student_gradebook | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | management-water_bill_reminder | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | mobility-accessible_grade1_walks | 很可能/合理场景 | A | 低 | 中-高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | mobility-mouse_keys_dubai_shortest_walking_route | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | mobility-mouse_keys_google_maps_route | 很可能/合理场景 | A | 高 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | mobility-nearest_accessible_beach | 很可能/合理场景 | A | 高 | 中-高 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | service-accessible_transport_request | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | service-bank_investigation_period | 很可能/合理场景 | A | 低 | 中 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | service-passport_application_post_office | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | service-reddit_monitor_post_count | 可能但偏低频/资料题 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| motor | service-voter_certificate_link | 很可能/合理场景 | A | 低 | 低 | 指令已用第一人称说明输入障碍，并把辅助功能保留为用户后续可用状态 |
| visual | access-chrome_zoom_150 | 很可能/合理场景 | A | 中 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-high_contrast_aquatic | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_color_filter_grayscale_inverted | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_color_filter_protanopia | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_font_size_140 | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_magnifier_200 | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_magnifier_open | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | access-windows_narrator_open | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | captcha-audio_4 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-click_sequence_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-count_chars_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-distorted_text_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-geometry_click_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-hold_button_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-image_recognition_1 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-math_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-patch_select_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-robot_checkbox_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | captcha-slide_puzzle_2 | 条件性（会遇到验证，但具体题型偏测试） | C | 低 | 低 | 适合作为障碍压力测试，不像用户独立提出的完整生活目标 |
| visual | communication-add_contact | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | communication-community_event_rsvp | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | communication-webinar_flyer_email | 很可能/合理场景 | B | 低 | 中 | 可执行且与视觉信息有关，但更像资料抽取/辨认题而非明确生活后续目的 |
| visual | consumption-keto_bread | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | consumption-lavender_coupon | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | consumption-marshmallow_bunnies | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | consumption-saute_pan | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | consumption-swingset_price_filter | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | consumption-toothbrush_price_comparison | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | health-drug_facts_package | 很可能/合理场景 | B | 低 | 中 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |
| visual | health-hospital_wayfinding_map | 很可能/合理场景 | B | 低 | 高 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |
| visual | health-nutrition_facts_label | 很可能/合理场景 | B | 低 | 中 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |
| visual | information-apple_q3_operating_margin | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | information-cat_image_alt_text | 很可能/合理场景 | B | 低 | 低 | 文档无障碍创作真实；对盲人代理场景需说明由代理描述、用户负责发布 |
| visual | information-cta_rail_map_alt_text | 很可能/合理场景 | B | 低 | 低 | 文档无障碍创作真实；对盲人代理场景需说明由代理描述、用户负责发布 |
| visual | information-invitation_image_alt_text | 很可能/合理场景 | B | 低 | 低 | 文档无障碍创作真实；对盲人代理场景需说明由代理描述、用户负责发布 |
| visual | information-metal_density_comparison | 可能但偏低频/资料题 | B | 低 | 低 | 可执行且与视觉信息有关，但更像资料抽取/辨认题而非明确生活后续目的 |
| visual | information-second_gold_rush | 可能但偏低频/资料题 | B | 低 | 低 | 可执行且与视觉信息有关，但更像资料抽取/辨认题而非明确生活后续目的 |
| visual | information-town_southeast_of_brisbane | 可能但偏低频/资料题 | B | 低 | 低 | 可执行且与视觉信息有关，但更像资料抽取/辨认题而非明确生活后续目的 |
| visual | information-wikipedia_image_person | 可能但偏低频/资料题 | B | 低 | 低 | 可执行且与视觉信息有关，但更像资料抽取/辨认题而非明确生活后续目的 |
| visual | management-cardiology_appointment_reminder | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | management-package_delivery_calendar | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | management-utility_bill_summary | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | management-weekly_planner_calendar | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | mobility-cta_airport_transfer | 很可能/合理场景 | A | 低 | 中 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | mobility-nearest_pharmacy_marina_bay_sands | 很可能/合理场景 | A | 低 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | mobility-transit_route_grand_central_to_liberty | 很可能/合理场景 | A | 高 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | mobility-walking_route_wat_arun | 很可能/合理场景 | A | 高 | 低 | 目标、辅助需求与持久结果基本一致，属于合理桌面使用场景 |
| visual | service-accessible_parking_renewal_notice | 很可能/合理场景 | B | 低 | 低 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |
| visual | service-medicare_card_sample | 很可能/合理场景 | B | 低 | 中 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |
| visual | service-real_id_infographic | 很可能/合理场景 | B | 低 | 中 | 视觉资料转为持久文本是合理代理任务，但当前指令偏字段抽取式 |

## 运行时高风险网页/服务

- 动态交互数据、扩展商店、下载或政府服务流程；其目标动作不能由静态 PDF 等价替代：`access-chrome_immersive_reader_extension`, `health-allied_health_form_download`, `information-ftc_2024_fraud_reports`, `information-ftc_florida_fraud_data`, `information-ftc_washington_q4_fraud`, `mobility-nearest_accessible_beach`, `service-irs_ip_pin_alternative_form`, `service-ssa_replacement_card_start`。
- 原先从实时文章逐字/按顺序抽取的 12 个任务已改为本地 PDF，不再属于运行时网页风险。
- 依赖 Google Maps / Street View / vclock 等在线交互状态；路线、UI、地点实体或服务可变：`health-wheelchair_charging_timer`, `management-double_dough_timer`, `management-dryer_cycle_timer`, `management-medication_timer`, `management-quick_sponge_timer`, `mobility-mouse_keys_google_maps_route`, `mobility-opera_house_street_view`, `mobility-transit_route_grand_central_to_liberty`, `mobility-walking_route_alhambra`, `mobility-walking_route_wat_arun`, `mobility-zion_large_group_route`。

### 高风险 URL / 平台归并

- Chrome Web Store 扩展页：`https://chromewebstore.google.com/detail/immersive-reader/cccnhdbjafjobcppogeaaabofifbpdho`。
- 动态目录/下载页：SIRA AHTR 仍需在线下载；Accessible Beaches NSW 仍需交互式筛选和查看卡片；NSW National Parks access-friendly tracks 已本地化。
- 逐字事实页：FTC gift-card / spam-text guidance、AP News 三个 article 固定链接、SELF hydration packs、Ready.gov kit、CFPB automatic payments、Incline Health appointment guide、Covey hobbies 均已本地化。
- 交互数据/政务流程：FTC Explore Data + Tableau、IRS IP PIN、SSA replacement card、Census data。
- 第三方交互平台：`https://www.google.com/maps`、`https://vclock.com`；前者路线和地点实体会变，后者 UI/计时器状态评测会变。
- 公网媒体：CDC、MedlinePlus、Canada.ca、NOAA、NPS、Rick Steves、World Heritage Journey；页面仍在不等于媒体直链、字幕轨和播放控件稳定。

## 原始出处高风险但通常不影响当前运行

- `mobility-babson_bow_shuttle_plan`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。
- `mobility-harvard_mather_evening_plan`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。
- `mobility-victoria_train_interchange_note`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。
- `mobility-wmata_a49_morning_plan`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。
- `communication-filter_keys_volunteer_email`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。
- `health-hospital_wayfinding_map`：年度/版本化 PDF 或站点上传路径会被下一年度文件替代；当前任务若使用本地副本仍可运行，但来源可追溯性会下降。

## 元数据与集合一致性问题

- 19 个仍依赖高风险交互网页/服务的任务中，现有 `possibility_of_env_change` 仍标为 `low` 的有 12 个：`health-wheelchair_charging_timer`, `information-ftc_2024_fraud_reports`, `information-ftc_florida_fraud_data`, `information-ftc_washington_q4_fraud`, `management-double_dough_timer`, `management-dryer_cycle_timer`, `management-medication_timer`, `management-quick_sponge_timer`, `mobility-mouse_keys_google_maps_route`, `mobility-opera_house_street_view`, `mobility-transit_route_grand_central_to_liberty`, `mobility-walking_route_alhambra`。建议拆成 `runtime_dependency_risk` 与 `source_provenance_risk` 两列。
- 若干 `proxy: true` 任务实际上只访问本地文件/`host.docker.internal`，另一些 `proxy: false` 任务保留了可能失效的公网出处。`proxy` 适合表示运行网络需求，不能代替网页漂移标签。

## 已本地化网页

- `information-skill_building_hobbies`：Covey 页面已保存为保留屏幕版式和图片、并附可搜索文本层的本地 PDF，任务改为 `file:///` 打开，`proxy` 改为 `false`。
- `mobility-accessible_grade1_walks`：NSW National Parks 完整步道列表已保存为保留屏幕版式和图片、并附可搜索文本层的本地 PDF；其中仍保留不符合筛选条件的条目。任务改为 `file:///` 打开，`proxy` 改为 `false`。
- `health-physiotherapy_appointment_checklist`：Incline Health 页面已保存为保留屏幕版式和图片、并附可搜索文本层的本地 PDF；原网页不再是运行依赖。该任务仍因 Thunderbird profile 下载保留 `proxy: true`。
- 新增本地化 12 个高风险内容型任务：`communication-ftc_gift_card_pressure_email`, `communication-ftc_gift_card_scam_email`, `communication-ftc_spam_text_safety_email`, `health-doctor_appointment_preparation`, `health-doctor_visit_preparation_summary`, `health-running_hydration_guide_note`, `health-sunscreen_ingredient_age_note`, `information-emergency_kit_checklist`, `information-passport_renewal_checklist`, `information-running_hydration_note`, `management-cfpb_autopay_review_reminder`, `management-sunscreen_ingredient_reminder`。
- Chrome 扩展安装、表单下载、FTC Tableau、Accessible Beaches 目录、IRS/SSA 流程、vclock、Google Maps/Street View 等交互型任务未转为 PDF；静态快照无法保留安装、下载、计时、筛选、路线和导航目标状态。

## 指令自然化

- 200 个任务的 `instruction` 均已改为从目标用户的实际障碍或支持需求出发，同时保留 evaluator 所需的文件名、标题、日期、地址、固定文本和最终状态。
- motor 指令说明物理键盘、组合键、重复击键或精细鼠标控制困难；visual/hearing 指令说明视觉或听觉获取障碍；cognitive 指令说明简化、持久记录或时间提醒的用途。
- CAPTCHA 统一描述为当前工作流中阻碍用户继续操作的验证步骤，仍作为 stress-test slice 单独看待。

## 优先修改建议

1. 将所有运行时高风险的事实抽取任务改成已固定的本地快照，或记录内容哈希、抓取日期和 canonical answer 版本；在线服务导航任务则用语义状态评测，避免固定 DOM/完整 URL。
2. motor 复合任务应把 AT 与主目标建立因果关系，例如“因为无法稳定使用物理键盘，请留下 OSK 供我继续填写”，而不是统一前缀式地要求开启设置。
3. CAPTCHA 任务在论文和统计中独立报告为 stress test；视觉/听觉 CAPTCHA 应提供或明确验证替代通道，否则是在测障碍本身，不是在测自然代理任务。
4. cognitive 任务减少“逐字复制、网页顺序、固定四项”等机械约束，改为用户真正需要的短清单、提醒或简明说明，同时让 evaluator 接受语义等价表达。
5. 对年度交通表、医院地图、志愿者目录保留本地副本并在任务 ID/元数据中显式写版本；到期后不要静默替换，否则 ground truth 会漂移。
6. 第三方 Chrome 扩展任务优先改为受控扩展包或 Edge 内置阅读功能，避免商店下架、权限提示和开发者变更。

## 当前网页抽查说明

- 2026-10-09 抽查时，SIRA AHTR、Accessible Beaches NSW、NSW National Parks、FTC、SELF、SSA、IRS、CDC、NOAA、NPS、WMATA、Babson 等页面仍可访问。
- `ready.gov/kit` 在抓取工具中返回内部错误，应视作至少中高风险并人工在目标 VM 复核。
- Harvard shuttle PDF 和 Victoria train map 的直链在抓取工具中不可访问；即使只是工具限制，也说明直链可移植性较差，应保留本地快照。
- Chrome Web Store 的 Immersive Reader 当前存在，但页面显示用户量很小且由个人开发者提供，稳定性和供应链风险高于内置功能。
