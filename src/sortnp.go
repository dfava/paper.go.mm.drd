// In-place parallel sorting
//
// author:    Daniel S. Fava
// email:     danielsf@ifi.uio.no
// contact:   www.danielfava.com
// copyright: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
// date:      April 2020
//
// See https://github.com/dfava/paper.go.mm.drd

package main

import(
  "sort"
  "math/rand"
)

var N = 40

//go:noinline
func swap(a[] int, fst int, snd int) {
  tmp := a[fst]
  a[fst] = a[snd]
  a[snd] = tmp
}

//go:noinline
func bubble(a[] int, fst int, snd int) {
  tmp := a[snd]
  for top := snd; top > fst; top-- {
    a[top] = a[top-1]
  }
  a[fst] = tmp
}

func merge(a[] int, fst int, snd int, lng int) {
  for (fst < snd && snd < lng) {
    if (a[fst] > a[snd]) {
      bubble(a, fst, snd)
      fst += 1
      snd += 1
      continue
    }
    fst += 1
  }
}

// parMerge can start when the two sections of the slice
// have been sorted individually,
// meaning it is no longer blocked on `<-c; <-c`
// parMerge signals that it is done via `done <- true`
func parMerge(a[] int, fst int, snd int, lng int, c chan bool, done chan bool) {
  <- c; <- c
  merge(a, fst, snd, lng)
  done <- true
}

func split(a[] int, fst int, lng int, done chan bool){
  if lng-fst > N+1 {
    cdone := make (chan bool, 2)
    mid := (fst + lng) / 2
    go split(a, fst, mid, cdone)
    go split(a, mid, lng, cdone)
    parMerge(a, fst, mid, lng, cdone, done)
  } else {
    sort.Slice(a[fst:lng], func(i,j int) bool { return a[fst+i] < a[fst+j]} )
    done <- true
  }
}

func main() {
  sz := 10000
  slc := make([]int, sz)
  for i := 0; i < sz; i++ {
    slc[i] = rand.Int()
  }
  c := make (chan bool, 2)
  split(slc, 0, len(slc), c)
  <- c
}
