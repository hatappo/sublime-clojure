#!/usr/bin/env inlein

'{:dependencies [[org.clojure/clojure "1.8.0"]
                 [enlive "1.1.6"]]}

(require '[net.cgrand.enlive-html :as html])
(require '[clojure.java.io :as io])
(require '[clojure.string :as s])

(def indent "    ")

(defn- fmt [coll]
  (->> coll
    (sort-by (comp s/lower-case first))
    dedupe
    (group-by (comp s/lower-case first))
    sort
    (map #(s/join "\",\"" (last %)))
    (s/join (str "\",\n" indent "\""))
    (format (str indent "\"%s\","))))

;; clj

(def clj-namespace-selector [:ul.nav :> :li :> :a html/text-node])

(def clj-var-selector [:ul.var-list :> :li :> :a html/text-node])

(defn scrape-clj-completions []
  (let [nodes (html/html-resource (io/reader "https://clojuredocs.org/core-library/vars"))]
    (println (str indent "// Namespaces"))
    (->> (html/select nodes clj-namespace-selector)
      (filter #(s/starts-with? % "clojure."))
      fmt
      println)
    (println (str indent "// Vars"))
    (->> (html/select nodes clj-var-selector)
      (filter #(< 1 (count %)))
      fmt
      println)))

;; cljs

(def cljs-namespace-selector [:h4 :> :a html/text-node])

(def cljs-var-selector [:span :> :a])

(defn scrape-cljs-completions []
  (let [nodes (html/html-resource (io/reader "http://cljs.github.io/api/"))]
    (println (str indent "// Namespaces"))
    (->> (html/select nodes cljs-namespace-selector)
      (filter #(re-matches #"^(cljs\.|clojure\.).*" %))
      fmt
      println)
    (println (str indent "// Vars"))
    (->> (html/select nodes cljs-var-selector)
      (map (fn [scraped] {:text (s/join "" (:content scraped))
                          :href (get-in scraped [:attrs :href])}))
      (filter #(and (< 1 (count (:text %)))
                    (re-matches #"^/api/(special|cljs\.|clojure\.).*" (:href %))))
      (map #(:text %))
      fmt
      println)))

;; main 

(condp = (first *command-line-args*)
  "clj"  (scrape-clj-completions)
  "cljs" (scrape-cljs-completions)
  (do (scrape-clj-completions)
      (scrape-cljs-completions)))
