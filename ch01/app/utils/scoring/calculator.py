from ch01.app.config.settings import settings

def calculate_soft_f1(
    user_style_tags: tuple[float, ...],
    tourist_style_tags: tuple[float, ...]
) -> float:

    user_theshold = settings.get_tag_threshold(
        "user_input_threshold"
    )
    overview_threshld = settings.get_tag_threshold(
        "tourist_description_threshold"
    )

    tp = 0.0
    fp = 0.0
    fn = 0.0

    for i in range(len(user_style_tags)):
        user_style_tag_bool = user_style_tags[i] >= user_theshold
        tourist_style_tag_bool = tourist_style_tags[i] >= overview_threshld
        
        if user_style_tag_bool and tourist_style_tag_bool:
            tp += user_style_tags[i] * tourist_style_tags[i]
        elif user_style_tag_bool and not tourist_style_tag_bool:
            fp += user_style_tags[i] * (1 - tourist_style_tags[i])
        elif not user_style_tag_bool and tourist_style_tag_bool:
            fn += tourist_style_tags[i] * (1 - user_style_tags[i])

    denominator = 2 * tp + fp + fn

    soft_f1 = (2 * tp) / denominator if denominator != 0.0 else 0.0

    return soft_f1

def calculate_recommendation_score(
    tag_score: float,
    similarity: float,
) -> float:
    tag_weight = settings.tag_weight
    similarity_weight = settings.similarity_weight
    normalized_similarity = (similarity + 1) / 2
    final_score = tag_score * tag_weight + normalized_similarity * similarity_weight
    return final_score