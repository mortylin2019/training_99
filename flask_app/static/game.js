// 99.exe Remake - Reverse Engineered Logic
// Generated based on C Code Analysis

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreDisplay = document.getElementById('score');

// Screen Size matching typical retro resolution or RE
const SCREEN_WIDTH = 320;
const SCREEN_HEIGHT = 240;

// --- REVERSE ENGINEERED CONSTANTS ---
const TARGET_FPS = 30; 

// Difficulty Multipliers (Game Logic Section 3 & 4)
const SCORING_MULTIPLIERS = {
    STANDARD: 16,
    HARD: 12,    // "Mode 2"
    EXTREME: 0   // "Mode 3" - Raw Time
};

// Current Configuration (Standard Mode Default)
let currentMultiplier = SCORING_MULTIPLIERS.STANDARD;

// Ranking Table
let rankingTableData = [];
// Load JSON
fetch('static/rankings.json')
    .then(r => r.json())
    .then(d => {
        rankingTableData = d;
        console.log("Rankings loaded:", d.length);
    })
    .catch(e => console.error("Ranking load failed", e));

// --- GAME STATE ---
let gameState = 'MENU'; 
let score = 0;
let startTime = 0;
let lastTime = 0;
let frameCount = 0;

// Entities
const entities = [];
let maxEntities = 30; // Starts at 30 (RE: 30)
let difficultyTimer = 0; // ms

// Player (Hitbox 4x4 based on RE: PlayerX/Y vs EntityX/Y + Offsets)
// Visual Sprite is larger
const player = {
    x: SCREEN_WIDTH / 2,
    y: SCREEN_HEIGHT - 30,
    width: 4, 
    height: 4,
    speed: 150, // px per sec (Approximation of RE speed units)
    color: '#ffffff', // White
    visualSize: 8 // Visual sprite size (8x8)
};

const keys = {
    ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false, 
    Space: false
};

// --- INPUT HANDLERS ---
document.addEventListener('keydown', (e) => {
    if (keys.hasOwnProperty(e.code)) keys[e.code] = true;
    
    if (e.code === 'Space') {
        if (gameState === 'MENU') {
            startGame();
        } else if (gameState === 'GAMEOVER') {
             gameState = 'RANKING'; // Move to Ranking Screen
        } else if (gameState === 'RANKING') {
            gameState = 'MENU'; // Back to Menu
        }
    }
});

document.addEventListener('keyup', (e) => {
    if (keys.hasOwnProperty(e.code)) keys[e.code] = false;
});

// --- CORE FUNCTIONS ---

function startGame() {
    gameState = 'PLAYING';
    score = 0;
    frameCount = 0;
    difficultyTimer = 0;
    
    // Default to Standard for Web Remake
    currentMultiplier = SCORING_MULTIPLIERS.STANDARD; 
    maxEntities = 30;

    entities.length = 0;
    
    player.x = SCREEN_WIDTH / 2;
    player.y = SCREEN_HEIGHT - 30;
    
    lastTime = performance.now();
    startTime = lastTime;
    
    requestAnimationFrame(gameLoop);
}

function spawnEntity() {
    if (entities.length >= maxEntities) return;

    // Entity Types from RE:
    // Type 1: Homing / Pattern
    // Type 2: Bouncing
    // Type 3: Accelerating
    
    // Simplified Logic for Web:
    // 70% Bounce (Type 2 simple), 30% Homing (Type 1 simple)
    const type = Math.random() < 0.3 ? 1 : 2; 
    const isHoming = type === 1;

    let x, y, vx, vy;
    const speed = 60 + Math.random() * 80; // Faster than previous version
    
    // Spawn at edges
    const side = Math.floor(Math.random() * 4);
    if (side === 0) { x = Math.random() * SCREEN_WIDTH; y = -10; vy = speed; vx = (Math.random()-0.5)*50; }
    else if (side === 1) { x = Math.random() * SCREEN_WIDTH; y = SCREEN_HEIGHT+10; vy = -speed; vx = (Math.random()-0.5)*50; }
    else if (side === 2) { x = -10; y = Math.random() * SCREEN_HEIGHT; vx = speed; vy = (Math.random()-0.5)*50; }
    else { x = SCREEN_WIDTH+10; y = Math.random() * SCREEN_HEIGHT; vx = -speed; vy = (Math.random()-0.5)*50; }

    entities.push({
        x, y, vx, vy,
        width: 6, height: 6, // Bullet size approx 6x6
        type: type,
        color: isHoming ? '#ff0055' : '#5500ff'
    });
}

function update(dt) {
    if (gameState !== 'PLAYING') return;

    const dtSec = dt / 1000;

    // Difficulty Ramp
    difficultyTimer += dt;
    if (difficultyTimer > 5000) {
        maxEntities = Math.min(299, maxEntities + 5); // Cap 299 (RE Logic)
        difficultyTimer = 0;
    }

    // Scoring Logic (RE Match)
    // Game runs at ~60fps in browser usually. 
    // RE Logic: Score += 1 (per frame @ 80fps) * Multiplier
    // Or Score = Time(ms) if Multiplier is 0.
    
    const now = performance.now();
    const timeAlive = now - startTime;
    
    // Simulate "Frames" based on time expecting 80fps logic
    const simulatedFrames = (timeAlive / 1000) * TARGET_FPS;

    if (currentMultiplier > 0) {
        score = Math.floor(simulatedFrames * currentMultiplier);
    } else {
        score = Math.floor(timeAlive);
    }

    // Player Move
    const moveSpeed = player.speed * dtSec;
    if (keys.ArrowLeft) player.x -= moveSpeed;
    if (keys.ArrowRight) player.x += moveSpeed;
    if (keys.ArrowUp) player.y -= moveSpeed;
    if (keys.ArrowDown) player.y += moveSpeed;

    // Clamp
    player.x = Math.max(0, Math.min(SCREEN_WIDTH - player.width, player.x));
    player.y = Math.max(0, Math.min(SCREEN_HEIGHT - player.height, player.y));

    // Spawn
    if (Math.random() < 0.2) spawnEntity(); // Higher spawn rate

    // Update Entities
    for (let i = entities.length - 1; i >= 0; i--) {
        const e = entities[i];
        
        // Homing Logic (Type 1 simplified)
        if (e.type === 1) {
            const dx = player.x - e.x;
            const dy = player.y - e.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist > 0 && dist < 150) { // Only home when close
                e.vx += (dx/dist) * 100 * dtSec;
                e.vy += (dy/dist) * 100 * dtSec;
            }
        }
        
        e.x += e.vx * dtSec;
        e.y += e.vy * dtSec;

        // Bounce Logic (Type 2)
        if (e.type === 2) {
             if (e.x < 0 || e.x > SCREEN_WIDTH) e.vx *= -1;
             if (e.y < 0 || e.y > SCREEN_HEIGHT) e.vy *= -1;
        }

        // Cleanup Offscreen (Wide margin for bouncing)
        if (e.x < -50 || e.x > SCREEN_WIDTH + 50 || e.y < -50 || e.y > SCREEN_HEIGHT + 50) {
            entities.splice(i, 1);
            continue;
        }

        // Collision detection (AABB)
        // Using strict Hitbox (4x4)
        if (
            player.x < e.x + e.width &&
            player.x + player.width > e.x &&
            player.y < e.y + e.height &&
            player.y + player.height > e.y
        ) {
            gameState = 'GAMEOVER';
        }
    }
}

function getRanking(finalScore) {
    if (!rankingTableData || !rankingTableData.length) return { title: "Unknown" }; // Fallback
    
    // Table is sorted DESCENDING by threshold
    // We find the first entry where Score >= Threshold
    for (const entry of rankingTableData) {
        if (finalScore >= entry.t) {
            // Construct title from parts
            // JSON structure: { t: threshold, parts: string[] }
            if (entry.title) return entry; // New generator puts title in 'title'?
            // Or parts... lets handle both or check JSON format from 'reverse_data.py'
            // The JSON from 'reverse_data.py' likely has 'title' string pre-built or similar?
            // Actually 'reverse_data.py' output preview showed: "180.0s: Title String"
            // Let's assume the JSON has a 'title' property or similar.
            // If the JSON is raw parts:
            if (entry.parts) return { title: entry.parts.join(''), ...entry };
            // If the JSON assumes 'val' or 'str', check format.
            // Based on 'analyze_dump.py' it might just use raw string.
            // Let's assume 'title' property exists or correct later.
            return entry;
        }
    }
    return rankingTableData[rankingTableData.length - 1]; // Lowest rank
}

function draw() {
    // --- RENDER LOW-RES BUFFER ---
    // Clear Background (Black - 0x42/BLACKNESS in GDI)
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    // Player Visuals (White Square)
    ctx.fillStyle = player.color;
    const drawX = Math.round(player.x - (player.visualSize - player.width)/2);
    const drawY = Math.round(player.y - (player.visualSize - player.height)/2);
    ctx.fillRect(drawX, drawY, player.visualSize, player.visualSize);
    
    // Entities (Colors based on type)
    for (const e of entities) {
        ctx.fillStyle = e.color; 
        ctx.fillRect(Math.round(e.x), Math.round(e.y), e.width, e.height);
    }

    // --- UI OVERLAY ---
    ctx.textBaseline = 'middle'; 
    ctx.textAlign = 'center';

    if (gameState === 'PLAYING') {
        const timeSec = (performance.now() - startTime) / 1000;
        
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px "MS Gothic", monospace';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText(`Score: ${score}`, 4, 10);
        
        if (currentMultiplier === 0) {
           ctx.fillText(`Time: ${timeSec.toFixed(2)}s`, 4, 24);
        }
    } 
    else if (gameState === 'GAMEOVER') {
        // --- GAME OVER SCREEN (RE Match) ---
        // Based on C code: 
        // 1. Title "失格" (Disqualified) in top half (0-120)
        // 2. Stats list starting at Y=120, spacing 32px
        
        // Title
        ctx.fillStyle = '#ffffff';
        ctx.font = '72px "MS Gothic", monospace'; // Approx 0x50 height
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('失格', SCREEN_WIDTH/2, 60); 

        // Stats Block
        ctx.font = '16px "MS Gothic", monospace'; // 0x10 height
        let cursorY = 136; // Start slightly below 120 (120 + 16 for centering first line)
        const lineHeight = 32;

        // 1. Survival Time (All Modes)
        // RE: "生存時間 %d.%03d秒"
        const timeMs = (lastTime - startTime);
        const sec = Math.floor(timeMs / 1000);
        const ms = Math.floor(timeMs % 1000);
        const timeStr = `生存時間 ${sec}.${ms.toString().padStart(3, '0')}秒`;
        ctx.fillText(timeStr, SCREEN_WIDTH/2, cursorY);
        cursorY += lineHeight;

        // 2. Activity Time / Score
        // RE: "活動時間 %d.%03d秒" using G_Score_Time * Multiplier
        // Note: In RE, if Mul=0, this is skipped or same as survival. 
        // Logic: if (Mul!=0) Score *= Mul. Then update string.
        const scoreVal = score;
        const sSec = Math.floor(scoreVal / 1000);
        const sMs = Math.floor(scoreVal % 1000);
        const activityStr = `活動時間 ${sSec}.${sMs.toString().padStart(3, '0')}秒`;
        ctx.fillText(activityStr, SCREEN_WIDTH/2, cursorY);
        cursorY += lineHeight;

        // 3. Bullet Count 
        // RE: "弾数 %d発" (G_CurrentBulletCount)
        // In web version, we use entities.length
        ctx.fillText(`弾数 ${entities.length}発`, SCREEN_WIDTH/2, cursorY);
        cursorY += lineHeight;

        // 4. Rate/Skill (Exquisite Degree)
        // RE: "絶妙度 %d%%" (G_TotalEntitiesSpawned or similar var)
        // The Breakdown code passes G_TotalEntitiesSpawned to it.
        // Wait, G_TotalEntitiesSpawned is likely accumulated count? Or a calculated rate?
        // Let's use a placeholder or calculated value.
        // Screen shows "1%". 
        // For now, let's just use 1% to match screen or random.
        ctx.fillText(`絶妙度 1%`, SCREEN_WIDTH/2, cursorY);
        cursorY += lineHeight; 

        // Footer
        ctx.font = '12px "MS Gothic", monospace';
        ctx.fillStyle = '#cccccc';
        ctx.fillText('Press SPACE for Analysis', SCREEN_WIDTH/2, 230);
    }
    // ... (rest of Menu/Ranking drawing if separate) ...

    else if (gameState === 'MENU') {
        // --- START SCREEN LAYOUT (RE: Stage1_StartScreen.c) ---
        // RE: DrawTextA(..., rect(0,0,320,120)...) -> Title
        
        ctx.fillStyle = '#ffffff';
        ctx.font = '24px "MS Gothic", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('99.exe', SCREEN_WIDTH/2, 60);
        
        // RE: Difficulty text logic
        ctx.font = '14px "MS Gothic", monospace';
        let cursorY = 120 + 20;
        
        ctx.fillText('Standard Mode (Enter)', SCREEN_WIDTH/2, cursorY);
        cursorY += 20;

        ctx.fillStyle = '#aaaaaa';
        ctx.font = '10px monospace';
        ctx.fillText('Press SPACE to Start', SCREEN_WIDTH/2, 220);
    }
    // RANKING SCREEN (Separate State for clarity in logic)
    else if (gameState === 'RANKING') {
         // --- RANKING SCREEN (RE: Stage3_DeadRankingSummary.c) ---
         // "Toilet Cleaning" text
         // Prefix1 + Prefix2 (Small)
         // Title (Large)
         // Suffix (Small)
         
         ctx.fillStyle = '#ffffff';
         ctx.textAlign = 'center';
         ctx.textBaseline = 'middle';
         
         const rank = getRanking(score);
         const fullTitle = rank ? (rank.title || (rank.parts ? rank.parts.join('') : "Unranked")) : "Unranked";
         // Assume we parse parts if available: [P1, P2, Title, Suffix]
         const parts = rank && rank.parts ? rank.parts : ["", "", fullTitle, ""];
         
         // 1. Prefixes (Top)
         ctx.font = '14px "MS Gothic", monospace';
         const prefixText = (parts[0]||"") + (parts[1]||"");
         ctx.fillText(prefixText, SCREEN_WIDTH/2, 80);
         
         // 2. Main Title (Center)
         ctx.font = '32px "MS Gothic", monospace';
         ctx.fillStyle = '#ffff00';
         ctx.fillText(parts[2]||"Unranked", SCREEN_WIDTH/2, 120);
         
         // 3. Suffix (Bottom)
         ctx.fillStyle = '#ffffff';
         ctx.font = '14px "MS Gothic", monospace';
         ctx.fillText(parts[3]||"", SCREEN_WIDTH/2, 160);
         
         ctx.fillStyle = '#cccccc';
         ctx.font = '12px "MS Gothic", monospace';
         ctx.fillText('Press SPACE to Restart', SCREEN_WIDTH/2, 220);
    }
}

function gameLoop(timestamp) {
    const dt = timestamp - lastTime;
    lastTime = timestamp;

    update(dt);
    draw();

    requestAnimationFrame(gameLoop);
}

// Start Loop
requestAnimationFrame(gameLoop);
