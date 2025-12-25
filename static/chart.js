class NatalChart {
    constructor(elementId, size) {
        this.container = document.getElementById(elementId);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
        this.ns = "http://www.w3.org/2000/svg";
        this.isMobile = size < 400;

        this.svg = document.createElementNS(this.ns, "svg");
        this.svg.setAttribute("width", size);
        this.svg.setAttribute("height", size);
        this.svg.style.display = "block";
        this.container.innerHTML = "";
        this.container.appendChild(this.svg);

        this.addDefs();

        this.signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
        
        // Цвета знаков как у Geocult (огонь-красный, земля-коричневый, воздух-зелёный, вода-синий)
        this.signTextColors = [
            "#d32f2f", "#5d4037", "#388e3c", "#1976d2",
            "#d32f2f", "#5d4037", "#388e3c", "#1976d2",
            "#d32f2f", "#5d4037", "#388e3c", "#1976d2"
        ];
        
        this.glyphColors = {
            Sun: "#ff6f00", Moon: "#5d4037", Mercury: "#795548", Venus: "#43a047",
            Mars: "#e53935", Jupiter: "#1565c0", Saturn: "#546e7a",
            Uranus: "#00838f", Neptune: "#5e35b1", Pluto: "#6a1b9a",
            North_node: "#37474f", South_node: "#37474f", Lilith: "#263238",
            Chiron: "#7b1fa2", ASC: "#1565c0", MC: "#1565c0"
        };
        this.planetIcons = {
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
            North_node: "☊", South_node: "☋", Lilith: "⚸", Chiron: "⚷",
            ASC: "AC", MC: "MC"
        };
    }

    addDefs() {
        const defs = document.createElementNS(this.ns, "defs");
        
        // Зелёный градиент для внешнего кольца (как у Geocult)
        const outerGrad = document.createElementNS(this.ns, "radialGradient");
        outerGrad.id = "outerGreen";
        outerGrad.innerHTML = '<stop offset="70%" stop-color="#e8f5e9"/><stop offset="100%" stop-color="#c8e6c9"/>';
        defs.appendChild(outerGrad);
        
        this.svg.appendChild(defs);
    }

    setAttr(el, attrs) {
        for (let k in attrs) el.setAttribute(k, attrs[k]);
    }

    draw(data) {
        if (!data || !data.houses || data.houses.length < 12) return;
        this.svg.innerHTML = "";
        this.addDefs();
        this.rotationOffset = 180 - (data.houses[0] || 0);
        this.houses = data.houses;
        
        const hasOuter = data.outerPlanets && data.outerPlanets.length > 0;
        
        // Расчёт радиусов
        const s = this.size;
        const m = this.isMobile;
        
        if (hasOuter) {
            this.rOuter = s/2 - 2;
            this.rTransitOuter = this.rOuter;
            this.rTransitInner = this.rOuter - (m ? 35 : 55);
            this.rTicksOuter = this.rTransitInner;
            this.rTicksInner = this.rTicksOuter - (m ? 12 : 18);
            this.rZodiacOuter = this.rTicksInner;
            this.rZodiacInner = this.rZodiacOuter - (m ? 28 : 42);
            this.rNatalOuter = this.rZodiacInner;
            this.rNatalInner = this.rNatalOuter - (m ? 25 : 40);
            this.rHouseOuter = this.rNatalInner;
            this.rAspect = this.rHouseOuter - (m ? 15 : 25);
            this.rInner = this.rAspect - (m ? 3 : 5);
        } else {
            this.rOuter = s/2 - 2;
            this.rTicksOuter = this.rOuter;
            this.rTicksInner = this.rOuter - (m ? 12 : 18);
            this.rZodiacOuter = this.rTicksInner;
            this.rZodiacInner = this.rZodiacOuter - (m ? 32 : 48);
            this.rNatalOuter = this.rZodiacInner;
            this.rNatalInner = this.rNatalOuter - (m ? 30 : 45);
            this.rHouseOuter = this.rNatalInner;
            this.rAspect = this.rHouseOuter - (m ? 18 : 28);
            this.rInner = this.rAspect - (m ? 3 : 5);
        }

        if (hasOuter) {
            this.drawTransitRing(data.outerPlanets);
        }
        this.drawTicksRing();
        this.drawZodiacRing();
        this.drawNatalPlanets(data.planets);
        this.drawHouseLines(data.houses);
        this.drawAxisLabels(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        this.drawCenterCircles();
        this.drawHouseNumbers(data.houses);
    }

    // Внешнее зелёное кольцо с транзитами
    drawTransitRing(planets) {
        // Зелёный фон
        const ring = document.createElementNS(this.ns, "circle");
        this.setAttr(ring, {cx: this.cx, cy: this.cy, r: this.rTransitOuter, fill: "url(#outerGreen)", stroke: "#a5d6a7", "stroke-width": "1"});
        this.svg.appendChild(ring);

        // Внутренняя граница транзитного кольца
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, {cx: this.cx, cy: this.cy, r: this.rTransitInner, fill: "#fff", stroke: "#9e9e9e", "stroke-width": "1"});
        this.svg.appendChild(inner);

        // Планеты в транзитном кольце
        if (!planets) return;
        const used = [];
        planets.forEach(p => {
            if (p.abs_pos === undefined) return;
            let angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            let r = (this.rTransitOuter + this.rTransitInner) / 2;

            for (let u of used) {
                if (Math.abs(angle - u.angle) < 0.15) r -= this.isMobile ? 10 : 14;
            }
            used.push({angle, r});

            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, {x, y, "text-anchor": "middle", "dominant-baseline": "central", 
                "font-size": this.isMobile ? "11" : "14", "font-weight": "bold", fill: "#37474f"});
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);

            // Маркер ретроградности
            if (p.is_retro) {
                const rx = x + (this.isMobile ? 7 : 10);
                const ry = y - (this.isMobile ? 5 : 7);
                const retro = document.createElementNS(this.ns, "text");
                this.setAttr(retro, {x: rx, y: ry, "font-size": this.isMobile ? "6" : "8", fill: "#d32f2f"});
                retro.textContent = "R";
                this.svg.appendChild(retro);
            }
        });
    }

    // Кольцо с градусными рисками
    drawTicksRing() {
        // Белый фон
        const bg = document.createElementNS(this.ns, "circle");
        this.setAttr(bg, {cx: this.cx, cy: this.cy, r: this.rTicksOuter, fill: "#fff", stroke: "#9e9e9e", "stroke-width": "1"});
        this.svg.appendChild(bg);

        // Красные риски каждый градус
        for (let deg = 0; deg < 360; deg++) {
            const angle = (deg + this.rotationOffset) * Math.PI / 180;
            const isMajor = deg % 5 === 0;
            const len = isMajor ? (this.isMobile ? 6 : 10) : (this.isMobile ? 3 : 5);
            
            const x1 = this.cx + this.rTicksOuter * Math.cos(angle);
            const y1 = this.cy + this.rTicksOuter * Math.sin(angle);
            const x2 = this.cx + (this.rTicksOuter - len) * Math.cos(angle);
            const y2 = this.cy + (this.rTicksOuter - len) * Math.sin(angle);
            
            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, {x1, y1, x2, y2, stroke: "#d32f2f", "stroke-width": isMajor ? "1" : "0.5"});
            this.svg.appendChild(line);
        }
    }

    // Кольцо знаков зодиака
    drawZodiacRing() {
        // Белый фон
        const bg = document.createElementNS(this.ns, "circle");
        this.setAttr(bg, {cx: this.cx, cy: this.cy, r: this.rZodiacOuter, fill: "#fff", stroke: "#9e9e9e", "stroke-width": "1"});
        this.svg.appendChild(bg);

        // Разделители знаков
        for (let i = 0; i < 12; i++) {
            const angle = (i * 30 + this.rotationOffset) * Math.PI / 180;
            const x1 = this.cx + this.rZodiacOuter * Math.cos(angle);
            const y1 = this.cy + this.rZodiacOuter * Math.sin(angle);
            const x2 = this.cx + this.rZodiacInner * Math.cos(angle);
            const y2 = this.cy + this.rZodiacInner * Math.sin(angle);
            
            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, {x1, y1, x2, y2, stroke: "#bdbdbd", "stroke-width": "1"});
            this.svg.appendChild(line);
        }

        // Символы знаков
        for (let i = 0; i < 12; i++) {
            const midAngle = ((i + 0.5) * 30 + this.rotationOffset) * Math.PI / 180;
            const r = (this.rZodiacOuter + this.rZodiacInner) / 2;
            const x = this.cx + r * Math.cos(midAngle);
            const y = this.cy + r * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, {x, y, "text-anchor": "middle", "dominant-baseline": "central",
                "font-size": this.isMobile ? "16" : "24", "font-weight": "bold", fill: this.signTextColors[i]});
            text.textContent = this.signs[i];
            this.svg.appendChild(text);
        }

        // Внутренняя граница
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, {cx: this.cx, cy: this.cy, r: this.rZodiacInner, fill: "#fff", stroke: "#9e9e9e", "stroke-width": "1"});
        this.svg.appendChild(inner);
    }

    // Натальные планеты
    drawNatalPlanets(planets) {
        if (!planets) return;
        const used = [];
        
        planets.forEach(p => {
            if (p.abs_pos === undefined) return;
            let angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            let r = (this.rNatalOuter + this.rNatalInner) / 2;

            for (let u of used) {
                if (Math.abs(angle - u.angle) < 0.18) r -= this.isMobile ? 12 : 16;
            }
            used.push({angle, r});

            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, {x, y, "text-anchor": "middle", "dominant-baseline": "central",
                "font-size": this.isMobile ? "12" : "16", "font-weight": "bold", fill: this.glyphColors[p.key] || "#424242"});
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);

            // Маркер ретроградности
            if (p.is_retro) {
                const rx = x + (this.isMobile ? 8 : 11);
                const ry = y - (this.isMobile ? 6 : 8);
                const retro = document.createElementNS(this.ns, "text");
                this.setAttr(retro, {x: rx, y: ry, "font-size": this.isMobile ? "7" : "9", fill: "#d32f2f", "font-weight": "bold"});
                retro.textContent = "R";
                this.svg.appendChild(retro);
            }
        });
    }

    // Линии домов
    drawHouseLines(houses) {
        for (let i = 0; i < 12; i++) {
            const angle = (houses[i] + this.rotationOffset) * Math.PI / 180;
            const isAngular = i % 3 === 0;
            
            const x1 = this.cx + this.rNatalInner * Math.cos(angle);
            const y1 = this.cy + this.rNatalInner * Math.sin(angle);
            const x2 = this.cx + this.rInner * Math.cos(angle);
            const y2 = this.cy + this.rInner * Math.sin(angle);
            
            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, {x1, y1, x2, y2, stroke: isAngular ? "#424242" : "#9e9e9e", "stroke-width": isAngular ? "2" : "1"});
            this.svg.appendChild(line);
        }
    }

    // Подписи осей AC/DC/MC/IC
    drawAxisLabels(houses) {
        const labels = [
            {idx: 0, text: "AC", offset: -20},
            {idx: 6, text: "DC", offset: 20},
            {idx: 9, text: "MC", offset: -15},
            {idx: 3, text: "IC", offset: 15}
        ];

        labels.forEach(l => {
            const angle = (houses[l.idx] + this.rotationOffset) * Math.PI / 180;
            const r = this.rOuter + (this.isMobile ? 12 : 18);
            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, {x, y, "text-anchor": "middle", "dominant-baseline": "central",
                "font-size": this.isMobile ? "10" : "14", "font-weight": "bold", fill: "#1565c0"});
            text.textContent = l.text;
            this.svg.appendChild(text);

            // Стрелка для AC
            if (l.idx === 0) {
                const arrowLen = this.isMobile ? 15 : 25;
                const ax1 = this.cx + (this.rOuter + 3) * Math.cos(angle);
                const ay1 = this.cy + (this.rOuter + 3) * Math.sin(angle);
                const ax2 = ax1 - arrowLen * Math.cos(angle);
                const ay2 = ay1 - arrowLen * Math.sin(angle);
                
                const arrow = document.createElementNS(this.ns, "line");
                this.setAttr(arrow, {x1: ax1, y1: ay1, x2: ax2, y2: ay2, stroke: "#1565c0", "stroke-width": "2"});
                this.svg.appendChild(arrow);
            }
        });
    }

    // Линии аспектов
    drawAspects(aspects, planets) {
        const posMap = {};
        planets.forEach(p => {
            if (p.abs_pos !== undefined) {
                posMap[p.key] = p.abs_pos;
                if (p.name) posMap[p.name] = p.abs_pos;
            }
        });

        // Цвета как у Geocult
        const colors = {
            Conjunction: "#4fc3f7", Sextile: "#66bb6a", Square: "#e53935",
            Trine: "#43a047", Opposition: "#d32f2f", Quincunx: "#26c6da"
        };

        aspects.forEach(a => {
            const pos1 = posMap[a.p1_key] ?? posMap[a.p1];
            const pos2 = posMap[a.p2_key] ?? posMap[a.p2];
            if (pos1 === undefined || pos2 === undefined) return;

            const angle1 = (pos1 + this.rotationOffset) * Math.PI / 180;
            const angle2 = (pos2 + this.rotationOffset) * Math.PI / 180;
            const r = this.rInner - 2;
            
            const x1 = this.cx + r * Math.cos(angle1);
            const y1 = this.cy + r * Math.sin(angle1);
            const x2 = this.cx + r * Math.cos(angle2);
            const y2 = this.cy + r * Math.sin(angle2);

            // Толщина линии зависит от орба
            const orb = Math.abs(a.orb || 0);
            const width = orb < 1 ? 2 : orb < 3 ? 1.5 : 1;

            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, {x1, y1, x2, y2, stroke: colors[a.type] || "#bdbdbd", "stroke-width": width});
            this.svg.appendChild(line);
        });
    }

    // Двойная окружность центра
    drawCenterCircles() {
        // Внешняя
        const outer = document.createElementNS(this.ns, "circle");
        this.setAttr(outer, {cx: this.cx, cy: this.cy, r: this.rInner, fill: "none", stroke: "#757575", "stroke-width": "1.5"});
        this.svg.appendChild(outer);

        // Внутренняя
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, {cx: this.cx, cy: this.cy, r: this.rInner - (this.isMobile ? 4 : 6), fill: "none", stroke: "#9e9e9e", "stroke-width": "1"});
        this.svg.appendChild(inner);
    }

    // Номера домов внутри центра
    drawHouseNumbers(houses) {
        for (let i = 0; i < 12; i++) {
            const nextHouse = houses[(i + 1) % 12];
            let midAngle = (houses[i] + nextHouse) / 2;
            if (nextHouse < houses[i]) midAngle = (houses[i] + nextHouse + 360) / 2;
            midAngle = (midAngle + this.rotationOffset) * Math.PI / 180;
            
            const r = this.rInner - (this.isMobile ? 12 : 18);
            const x = this.cx + r * Math.cos(midAngle);
            const y = this.cy + r * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, {x, y, "text-anchor": "middle", "dominant-baseline": "central",
                "font-size": this.isMobile ? "8" : "11", fill: "#757575"});
            text.textContent = (i + 1).toString();
            this.svg.appendChild(text);
        }
    }
}
