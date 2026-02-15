const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreDisplay = document.getElementById('score');

const SCREEN_WIDTH = 320;
const SCREEN_HEIGHT = 240;

// Game State
let gameState = 'MENU'; // MENU, PLAYING, GAMEOVER
let score = 0;
let lastTime = 0;

// Player
const player = {
    x: SCREEN_WIDTH / 2,
    y: SCREEN_HEIGHT - 30,
    width: 12,  // Slightly smaller hitbox for ship feeling
    height: 12, 
    speed: 150, // pixels per second
    color: '#ffffff' // White body
};

// Input
const keys = {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
    Space: false
};

// Entities
const entities = [];
let maxEntities = 30; // Starts at Easy (30)
let difficultyTimer = 0;

document.addEventListener('keydown', (e) => {
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = true;
    }
    if (e.code === 'Space' && gameState !== 'PLAYING') {
        startGame();
    }
});

document.addEventListener('keyup', (e) => {
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = false;
    }
});

function startGame() {
    gameState = 'PLAYING';
    score = 0;
    maxEntities = 30;
    difficultyTimer = 0;
    entities.length = 0;
    player.x = SCREEN_WIDTH / 2;
    player.y = SCREEN_HEIGHT - 30;
    lastTime = performance.now();
    requestAnimationFrame(gameLoop);
}

function spawnEntity() {
    if (entities.length >= maxEntities) return;

    let x, y, vx, vy;
    const speed = 30 + Math.random() * 50;
    
    // Random Spawn Position (Top, Bottom, Left, Right)
    const side = Math.floor(Math.random() * 4); // 0: Top, 1: Bottom, 2: Left, 3: Right
    
    if (side === 0) { // Top
        x = Math.random() * SCREEN_WIDTH;
        y = -10;
        vx = (Math.random() - 0.5) * 50;
        vy = speed;
    } else if (side === 1) { // Bottom
        x = Math.random() * SCREEN_WIDTH;
        y = SCREEN_HEIGHT + 10;
        vx = (Math.random() - 0.5) * 50;
        vy = -speed;
    } else if (side === 2) { // Left
        x = -10;
        y = Math.random() * SCREEN_HEIGHT;
        vx = speed;
        vy = (Math.random() - 0.5) * 50;
    } else { // Right
        x = SCREEN_WIDTH + 10;
        y = Math.random() * SCREEN_HEIGHT;
        vx = -speed;
        vy = (Math.random() - 0.5) * 50;
    }
    
    // Difficulty Progression Logic for Types
    // 0-10s: Mostly Bouncers (Type 2)
    // 10s+: Add Homers (Type 1)
    let type = 2; // Default Bouncer
    
    if (difficultyTimer > 10) {
        if (Math.random() < 0.3) type = 1; // 30% chance of Homer
    }
    if (difficultyTimer > 30) {
        if (Math.random() < 0.6) type = 1; // 60% chance of Homer
    }
    
    entities.push({
        x: x,
        y: y,
        width: 4, 
        height: 4,
        vx: vx,
        vy: vy,
        type: type,
        color: type === 1 ? '#ff0000' : (type === 2 ? '#ffff00' : '#00ffff') // Red, Yellow, Cyan
    });
}

function update(dt) {
    if (gameState !== 'PLAYING') return;

    // Difficulty Ramp
    difficultyTimer += dt;
    // Cap at Lunatic (200 entities)
    maxEntities = Math.min(200, 30 + Math.floor(difficultyTimer * 2));

    // Player Movement
    if (keys.ArrowLeft) player.x -= player.speed * dt;
    if (keys.ArrowRight) player.x += player.speed * dt;
    if (keys.ArrowUp) player.y -= player.speed * dt;
    if (keys.ArrowDown) player.y += player.speed * dt;

    // Clamp Player Position
    player.x = Math.max(0, Math.min(SCREEN_WIDTH - player.width, player.x));
    player.y = Math.max(0, Math.min(SCREEN_HEIGHT - player.height, player.y));

    // Spawn Entities
    if (Math.random() < 0.05) { // Spawn rate
        spawnEntity();
    }

    // Update Entities
    for (let i = entities.length - 1; i >= 0; i--) {
        const ent = entities[i];
        
        if (ent.type === 1) { // Homing
            const dx = player.x - ent.x;
            const dy = player.y - ent.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist > 0) {
                ent.vx += (dx / dist) * 100 * dt;
                ent.vy += (dy / dist) * 100 * dt;
                // Cap speed
                const speed = Math.sqrt(ent.vx*ent.vx + ent.vy*ent.vy);
                if (speed > 80) {
                    ent.vx = (ent.vx / speed) * 80;
                    ent.vy = (ent.vy / speed) * 80;
                }
            }
        } else if (ent.type === 2) { // Bouncing
            if (ent.x <= 0 || ent.x >= SCREEN_WIDTH - ent.width) {
                ent.vx *= -1;
            }
        }

        ent.x += ent.vx * dt;
        ent.y += ent.vy * dt;

        // Collision Check
        if (
            player.x < ent.x + ent.width &&
            player.x + player.width > ent.x &&
            player.y < ent.y + ent.height &&
            player.y + player.height > ent.y
        ) {
            gameState = 'GAMEOVER';
        }

        // Remove off-screen entities (Optimized boundaries)
        if (ent.y > SCREEN_HEIGHT + 50 || ent.y < -50 || ent.x < -50 || ent.x > SCREEN_WIDTH + 50) {
            entities.splice(i, 1);
            // No score for removing, score is time based
        }
    }
}

function draw() {
    // Clear Screen
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    
    // Draw Stars (Simple Static Background for "Vibe")
    ctx.fillStyle = '#444'; 
    for(let i=0; i<50; i++) {
        const sx = (i * 37) % SCREEN_WIDTH;
        const sy = (i * 19 + lastTime/50) % SCREEN_HEIGHT;
        ctx.fillRect(sx, sy, 1, 1);
    }

    if (gameState === 'MENU') {
        ctx.fillStyle = '#ffffff';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('TOKKUN REMAKE', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20);
        ctx.font = '14px Arial';
        ctx.fillText('Press SPACE to Start', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20);
        return;
    }

    if (gameState === 'GAMEOVER') {
        ctx.fillStyle = '#ff0000';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20);
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px Arial';
        
        // Rank / Rating based on time (score)
        let rank = "Civilian";
        if (score > 10) rank = "Trainee";
        if (score > 30) rank = "Soldier";
        if (score > 60) rank = "Veteran";
        if (score > 100) rank = "Ace Pilot";
        if (score > 1000) rank = "God";

        ctx.fillText(`Time: ${(score).toFixed(2)}s`, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10);
        ctx.fillText(`Rank: ${rank}`, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30);
        ctx.fillText('Press SPACE to Restart', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60);
        return;
    }

    // Draw Player (Ship Style)
    ctx.save();
    ctx.translate(player.x + player.width/2, player.y + player.height/2);
    // Body (White)
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.moveTo(0, -6);
    ctx.lineTo(4, 4);
    ctx.lineTo(-4, 4);
    ctx.fill();
    // Wings (Red)
    ctx.fillStyle = '#f00';
    ctx.beginPath();
    ctx.moveTo(-4, 2);
    ctx.lineTo(-7, 6);
    ctx.lineTo(-4, 4);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(4, 2);
    ctx.lineTo(7, 6);
    ctx.lineTo(4, 4);
    ctx.fill();
    
    // Engine Glow
    ctx.fillStyle = '#0ff';
    ctx.beginPath();
    ctx.moveTo(-2, 5);
    ctx.lineTo(0, 8);
    ctx.lineTo(2, 5);
    ctx.fill();
    ctx.restore();

    // Draw Entities (Glowing Dots)
    for (const ent of entities) {
        ctx.fillStyle = ent.color;
        
        ctx.beginPath();
        ctx.arc(ent.x + ent.width/2, ent.y + ent.height/2, ent.width/2, 0, Math.PI*2);
        
        // Simple Glow Effect
        // Note: extensive shadowBlur can be slow on Canvas, keeping it minimal
        ctx.shadowBlur = 4;
        ctx.shadowColor = ent.color;
        ctx.fill();
        ctx.shadowBlur = 0; // Reset
    }
    
    // Update Score Display HTML
    score = difficultyTimer; // Use survival time as score
    scoreDisplay.innerText = `Time: ${score.toFixed(2)}s`;
}

function gameLoop(timestamp) {
    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    update(dt);
    draw();

    if (gameState === 'PLAYING' || gameState === 'GAMEOVER') {
        requestAnimationFrame(gameLoop);
    }
}

// Initial Draw
draw();
