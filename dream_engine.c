// dream_engine.c
// Compile with: gcc -shared -o dream_engine.so -fPIC dream_engine.c -lm

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define MAX_SYMBOLS 100
#define MAX_SYMBOL_LENGTH 64
#define MAX_NARRATIVE_LENGTH 2048

// Psychological state structure
typedef struct {
    float fear_level;
    float tension_level;
    float anxiety_baseline;
    float confrontation_tendency;
    float avoidance_tendency;
    int dream_depth;
    int total_choices;
    float time_pressure;
} PsychState;

// Dream symbol with emotional weight
typedef struct {
    char name[MAX_SYMBOL_LENGTH];
    float emotional_weight;
    int occurrence_count;
    float fear_association;
    float comfort_association;
} DreamSymbol;

// Dream context for generation
typedef struct {
    PsychState state;
    DreamSymbol symbols[MAX_SYMBOLS];
    int symbol_count;
    int is_nightmare;
    float reality_distortion;
    unsigned int seed;
} DreamContext;

// Initialize random seed based on time and user factors
void init_dream_random(DreamContext* ctx, int user_id, long timestamp) {
    ctx->seed = (unsigned int)(user_id * 31337 + timestamp);
    srand(ctx->seed);
}

// Custom random float between 0 and 1
float dream_random(DreamContext* ctx) {
    ctx->seed = ctx->seed * 1103515245 + 12345;
    return (float)(ctx->seed % 10000) / 10000.0f;
}

// Calculate fear escalation based on choices and time
float calculate_fear_escalation(PsychState* state, int choice_type, float response_time) {
    float base_escalation = 0.0f;
    
    // Choice types: 0=neutral, 1=confront, 2=flee, 3=investigate, 4=ignore
    switch(choice_type) {
        case 1: // Confrontation reduces long-term fear but spikes tension
            base_escalation = -0.3f;
            state->tension_level += 0.5f;
            state->confrontation_tendency += 0.1f;
            break;
        case 2: // Fleeing increases fear over time
            base_escalation = 0.4f;
            state->avoidance_tendency += 0.15f;
            break;
        case 3: // Investigation - moderate increase, builds depth
            base_escalation = 0.2f;
            state->anxiety_baseline += 0.05f;
            break;
        case 4: // Ignoring - fear builds passively
            base_escalation = 0.3f;
            state->time_pressure += 0.2f;
            break;
        default:
            base_escalation = 0.1f;
    }
    
    // Faster responses indicate panic, amplify fear
    if (response_time < 2.0f) {
        base_escalation *= 1.5f;
    } else if (response_time > 10.0f) {
        // Slow responses indicate hesitation
        state->anxiety_baseline += 0.02f;
    }
    
    // Dream depth multiplier
    float depth_multiplier = 1.0f + (state->dream_depth - 1) * 0.25f;
    
    return base_escalation * depth_multiplier;
}

// Calculate tension based on narrative pacing
float calculate_tension(PsychState* state, float scene_duration, int has_threat) {
    float tension_change = 0.0f;
    
    // Tension naturally builds
    tension_change += 0.1f;
    
    // Threats spike tension
    if (has_threat) {
        tension_change += 0.4f * (1.0f + state->avoidance_tendency);
    }
    
    // Long scenes without resolution increase tension
    if (scene_duration > 60.0f) {
        tension_change += 0.2f;
    }
    
    // High fear compounds tension
    if (state->fear_level > 5.0f) {
        tension_change *= 1.0f + (state->fear_level - 5.0f) * 0.1f;
    }
    
    return tension_change;
}

// Determine if nightmare mode should trigger
int should_trigger_nightmare(PsychState* state, DreamContext* ctx) {
    float nightmare_threshold = 7.5f;
    
    // Avoidance behavior lowers threshold
    nightmare_threshold -= state->avoidance_tendency * 2.0f;
    
    // Deep dreams are more likely to become nightmares
    nightmare_threshold -= (state->dream_depth - 1) * 0.5f;
    
    // Random factor
    float random_factor = dream_random(ctx) * 2.0f;
    
    return (state->fear_level + random_factor) >= nightmare_threshold;
}

// Calculate reality distortion level (how surreal the dream becomes)
float calculate_distortion(PsychState* state, int scene_count) {
    float distortion = 0.0f;
    
    // Base distortion increases with depth
    distortion += state->dream_depth * 0.15f;
    
    // Fear causes more distortion
    distortion += state->fear_level * 0.05f;
    
    // Longer dreams become more unstable
    distortion += scene_count * 0.02f;
    
    // Tension warps reality
    distortion += state->tension_level * 0.03f;
    
    // Cap at 1.0
    return fminf(distortion, 1.0f);
}

// Analyze choice patterns and return psychological profile scores
void analyze_psychology(
    int* choice_history, 
    int choice_count, 
    float* response_times,
    float* out_confrontation,
    float* out_avoidance,
    float* out_curiosity,
    float* out_denial
) {
    int confront_count = 0;
    int flee_count = 0;
    int investigate_count = 0;
    int ignore_count = 0;
    float total_response_time = 0.0f;
    
    for (int i = 0; i < choice_count; i++) {
        total_response_time += response_times[i];
        
        switch(choice_history[i]) {
            case 1: confront_count++; break;
            case 2: flee_count++; break;
            case 3: investigate_count++; break;
            case 4: ignore_count++; break;
        }
    }
    
    float total = (float)choice_count;
    if (total < 1) total = 1;
    
    *out_confrontation = (float)confront_count / total;
    *out_avoidance = (float)flee_count / total;
    *out_curiosity = (float)investigate_count / total;
    *out_denial = (float)ignore_count / total;
    
    // Adjust based on response times
    float avg_response = total_response_time / total;
    
    // Fast responders are more reactive
    if (avg_response < 3.0f) {
        *out_confrontation *= 1.2f;
        *out_avoidance *= 1.2f;
    }
    // Slow responders are more deliberate
    else if (avg_response > 8.0f) {
        *out_curiosity *= 1.3f;
    }
}

// Calculate symbol emotional resonance
float calculate_symbol_resonance(DreamSymbol* symbol, PsychState* state) {
    float resonance = symbol->emotional_weight;
    
    // Frequent symbols have more impact
    resonance *= logf(1.0f + symbol->occurrence_count) / 2.0f;
    
    // Fear-associated symbols hit harder when fear is high
    if (state->fear_level > 3.0f) {
        resonance += symbol->fear_association * (state->fear_level / 10.0f);
    }
    
    // Comfort symbols provide relief
    resonance -= symbol->comfort_association * (1.0f - state->fear_level / 10.0f);
    
    return resonance;
}

// Select atmosphere based on psychological state
int select_atmosphere(PsychState* state, DreamContext* ctx) {
    // Atmospheres: 0=peaceful, 1=unsettling, 2=tense, 3=terrifying, 4=surreal, 5=void
    
    float roll = dream_random(ctx);
    float fear_normalized = state->fear_level / 10.0f;
    float tension_normalized = state->tension_level / 10.0f;
    
    if (ctx->is_nightmare) {
        if (roll < 0.3f) return 3; // terrifying
        if (roll < 0.6f) return 2; // tense
        return 4; // surreal
    }
    
    if (state->dream_depth >= 4) {
        if (roll < 0.4f) return 5; // void
        return 4; // surreal
    }
    
    if (fear_normalized > 0.7f) {
        return 3; // terrifying
    } else if (fear_normalized > 0.4f || tension_normalized > 0.6f) {
        return 2; // tense
    } else if (fear_normalized > 0.2f) {
        return 1; // unsettling
    }
    
    return roll < 0.7f ? 0 : 4; // peaceful or surreal
}

// Determine choice consequences
void calculate_choice_consequences(
    int choice_type,
    PsychState* state,
    DreamContext* ctx,
    float* fear_delta,
    float* tension_delta,
    int* depth_change,
    int* trigger_symbol
) {
    *fear_delta = calculate_fear_escalation(state, choice_type, 5.0f);
    *tension_delta = 0.0f;
    *depth_change = 0;
    *trigger_symbol = -1;
    
    // Certain choices deepen the dream
    if (choice_type == 3 && dream_random(ctx) < 0.3f) { // investigate
        *depth_change = 1;
    }
    
    // Confrontation may surface buried symbols
    if (choice_type == 1 && ctx->symbol_count > 0) {
        if (dream_random(ctx) < 0.4f) {
            *trigger_symbol = (int)(dream_random(ctx) * ctx->symbol_count);
        }
    }
    
    // Fleeing increases tension
    if (choice_type == 2) {
        *tension_delta = 0.5f;
    }
    
    // Ignoring lets tension build
    if (choice_type == 4) {
        *tension_delta = 0.3f;
        *fear_delta += 0.1f;
    }
}

// Export functions for Python ctypes
#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

EXPORT float c_calculate_fear_escalation(
    float fear_level, float tension_level, float anxiety_baseline,
    float confrontation_tendency, float avoidance_tendency,
    int dream_depth, int choice_type, float response_time
) {
    PsychState state = {
        .fear_level = fear_level,
        .tension_level = tension_level,
        .anxiety_baseline = anxiety_baseline,
        .confrontation_tendency = confrontation_tendency,
        .avoidance_tendency = avoidance_tendency,
        .dream_depth = dream_depth,
        .total_choices = 0,
        .time_pressure = 0.0f
    };
    return calculate_fear_escalation(&state, choice_type, response_time);
}

EXPORT float c_calculate_distortion(
    float fear_level, float tension_level, int dream_depth, int scene_count
) {
    PsychState state = {
        .fear_level = fear_level,
        .tension_level = tension_level,
        .dream_depth = dream_depth
    };
    return calculate_distortion(&state, scene_count);
}

EXPORT int c_should_nightmare(
    float fear_level, float avoidance_tendency, int dream_depth, int seed
) {
    PsychState state = {
        .fear_level = fear_level,
        .avoidance_tendency = avoidance_tendency,
        .dream_depth = dream_depth
    };
    DreamContext ctx = {.seed = seed};
    return should_trigger_nightmare(&state, &ctx);
}

EXPORT int c_select_atmosphere(
    float fear_level, float tension_level, int dream_depth, 
    int is_nightmare, int seed
) {
    PsychState state = {
        .fear_level = fear_level,
        .tension_level = tension_level,
        .dream_depth = dream_depth
    };
    DreamContext ctx = {
        .state = state,
        .is_nightmare = is_nightmare,
        .seed = seed
    };
    return select_atmosphere(&state, &ctx);
}

EXPORT void c_analyze_psychology(
    int* choices, float* times, int count,
    float* confrontation, float* avoidance, float* curiosity, float* denial
) {
    analyze_psychology(choices, count, times, 
                       confrontation, avoidance, curiosity, denial);
}
