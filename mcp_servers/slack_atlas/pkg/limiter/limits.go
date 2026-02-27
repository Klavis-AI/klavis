package limiter

import (
	"time"

	"golang.org/x/time/rate"
)

type tier struct {
	// once every
	t time.Duration
	// burst
	b int
}

func (t tier) Limiter() *rate.Limiter {
	return rate.NewLimiter(rate.Every(t.t), t.b)
}

var (
	// tier1 = tier{t: 1 * time.Minute, b: 2}
	// tier2 = tier{t: 3 * time.Second, b: 3}
	Tier2boost = tier{t: 300 * time.Millisecond, b: 5}
	Tier3      = tier{t: 1200 * time.Millisecond, b: 4}
	// tier4      = tier{t: 60 * time.Millisecond, b: 5}
)
